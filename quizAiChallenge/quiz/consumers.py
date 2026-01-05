import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Question
import redis.asyncio as redis
from redis.asyncio.lock import Lock as RedisLock

logger = logging.getLogger(__name__)

class QuizConsumer(AsyncWebsocketConsumer):
    redis_client = None
    
    @classmethod
    async def get_redis(cls):
        if cls.redis_client is None:
            cls.redis_client = await redis.from_url(
                'redis://localhost:6379',
                encoding='utf-8',
                decode_responses=True
            )
        return cls.redis_client

    def state_key(self, code):
        return f'quiz:room:{code}'
    
    def lock_key(self, code):
        return f'quiz:lock:{code}'
    
    async def get_state(self, code):
        redis_conn = await self.get_redis()
        data = await redis_conn.get(self.state_key(code))
        if data:
            state = json.loads(data)
            state.setdefault('active_players', [])
            state.setdefault('used_questions', [])
            state.setdefault('channel_to_player', {})
            state.setdefault('last_results_ack', [])
            return state
        return None
    
    async def set_state(self, code, state, ttl=3600):
        redis_conn = await self.get_redis()
        state_copy = state.copy()
        if 'last_results_ack' in state_copy and isinstance(state_copy['last_results_ack'], set):
            state_copy['last_results_ack'] = list(state_copy['last_results_ack'])
        await redis_conn.setex(self.state_key(code), ttl, json.dumps(state_copy))
    
    async def delete_state(self, code):
        redis_conn = await self.get_redis()
        await redis_conn.delete(self.state_key(code))
    
    async def get_redis_lock(self, code, timeout=10):
        redis_conn = await self.get_redis()
        return RedisLock(redis_conn, self.lock_key(code), timeout=timeout, blocking_timeout=timeout)

    # DB helpers
    @database_sync_to_async
    def get_room(self, code): return Room.objects.get(code=code)

    @database_sync_to_async
    def increment_player_count(self, code):
        room = Room.objects.get(code=code)
        room.player_count += 1
        room.save()
        return room

    @database_sync_to_async
    def decrement_player_count(self, code):
        room = Room.objects.get(code=code)
        room.player_count = max(0, room.player_count - 1)
        if room.player_count == 0:
            room.started = False
        room.save()
        return room

    @database_sync_to_async
    def mark_room_started(self, code):
        room = Room.objects.get(code=code)
        room.started = True
        room.save()

    @database_sync_to_async
    def mark_room_stopped(self, code):
        room = Room.objects.get(code=code)
        room.started = False
        room.save()

    @database_sync_to_async
    def get_random_unused_question(self, used_ids):
        qs = Question.objects.exclude(id__in=used_ids)
        if qs.exists():
            return qs.order_by('?').first()
        return Question.objects.order_by('?').first()

    async def connect(self):
        self.code = self.scope['url_route']['kwargs']['code']
        self.room_group_name = f'quiz_{self.code}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        try:
            await self.get_room(self.code)
        except Exception:
            await self.send(json.dumps({'type': 'no_room'}))
            await self.close()
            return

        room = await self.get_room(self.code)
        if room.started:
            await self.send(json.dumps({'type': 'error', 'message': 'Match already started'}))
            await self.close()
            return

        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if state is None:
                state = {
                    'question': None,
                    'question_num': 1,
                    'used_questions': [],
                    'active_players': [],
                    'player_label_snapshot': {},
                    'answers': {},
                    'answered_flags': {},
                    'auto_answered': {},
                    'channel_to_player': {},
                    'scores': {'player1': 0, 'player2': 0},
                    'timer_running': False,
                    'processing': False,
                    'processed': False,
                    'expected_players': 2,
                    'last_results_by_label': None,
                    'last_results_ack': [],
                }

            used = set(state['channel_to_player'].values())
            if 'player1' not in used:
                player = 'player1'
            elif 'player2' not in used:
                player = 'player2'
            else:
                await self.send(json.dumps({'type': 'error', 'message': 'Room full'}))
                await self.close()
                return

            state['channel_to_player'][self.channel_name] = player
            await self.set_state(self.code, state)

        room = await self.increment_player_count(self.code)

        await self.send(json.dumps({
            'type': 'joined',
            'player_label': player,
            'player_count': room.player_count,
        }))

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'player.joined', 'player_label': player}
        )

        # Resend last result on reconnect
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if state and state.get('last_results_by_label'):
                last = state['last_results_by_label']
                ack = set(state.get('last_results_ack', []))
                if player not in ack:
                    res = last['results'].get(player, {})
                    payload = {
                        'type': 'result',
                        'message': (f"Time up! Correct: {last.get('correct_answer')}"
                                    if res.get('timed_out')
                                    else f"Your answer: {res.get('your_answer')} {'✓' if res.get('is_correct') else '✗'}"),
                        'scores': last['scores'],
                        'question_num': last['question_num'],
                        'correct_answer': last.get('correct_answer')
                    }
                    await self.send(json.dumps(payload))

        # Start game when both joined
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if (state and len(state['channel_to_player']) == 2 and state.get('question') is None
                and not state.get('timer_running') and not state.get('processed')):
                await self.mark_room_started(self.code)
                asyncio.create_task(self.send_next_question())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.decrement_player_count(self.code)

        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if not state:
                return
            state['channel_to_player'].pop(self.channel_name, None)
            await self.set_state(self.code, state)

        if not any(state.get('channel_to_player', {})):
            await self.delete_state(self.code)
            await self.mark_room_stopped(self.code)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') != 'answer':
            return

        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if not state or self.channel_name not in state.get('active_players', []):
                return
            if state['answered_flags'].get(self.channel_name):
                return

            state['answered_flags'][self.channel_name] = True
            state['answers'][self.channel_name] = data['answer']
            state['auto_answered'][self.channel_name] = False

            answered_count = sum(state['answered_flags'].get(ch, False) for ch in state['active_players'])
            if answered_count == state.get('expected_players', 2) and not state.get('processing') and not state.get('processed'):
                state['processing'] = True
                state['timer_running'] = False
                await self.set_state(self.code, state)
                asyncio.create_task(self.process_answers())  # Run outside lock

            await self.set_state(self.code, state)

        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'player.answered', 'player_label': state['channel_to_player'].get(self.channel_name)}
        )

    async def send_next_question(self):
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if not state or state['question_num'] > 10:
                await self.channel_layer.group_send(self.room_group_name, {'type': 'match.finished', 'scores': state['scores']})
                await self.delete_state(self.code)
                return

            q = await self.get_random_unused_question(state['used_questions'])
            if not q:
                await self.channel_layer.group_send(self.room_group_name, {'type': 'match.finished', 'scores': state['scores']})
                return

            state['question'] = {'id': q.id, 'correct': getattr(q, 'correct', None)}
            state['used_questions'].append(q.id)
            state['active_players'] = list(state['channel_to_player'].keys())

            snapshot = {pl: ch for ch, pl in state['channel_to_player'].items()}
            snapshot.setdefault('player1', None)
            snapshot.setdefault('player2', None)
            state['player_label_snapshot'] = snapshot

            state['answers'] = {ch: None for ch in state['active_players']}
            state['answered_flags'] = {ch: False for ch in state['active_players']}
            state['auto_answered'] = {ch: False for ch in state['active_players']}
            state['processed'] = False
            state['processing'] = False
            state['timer_running'] = True

            question_payload = q.as_dict() if hasattr(q, 'as_dict') else {'text': q.text, 'a': q.a, 'b': q.b, 'c': q.c, 'd': q.d}

            await self.set_state(self.code, state)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'start.quiz',
                    'question': question_payload,
                    'question_num': state['question_num'],
                    'timer': 30,
                }
            )

        asyncio.create_task(self.start_timer())

    async def start_timer(self):
        await asyncio.sleep(30)
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if not state or not state.get('timer_running'):
                return
            for ch in state['active_players']:
                if not state['answered_flags'].get(ch):
                    state['answered_flags'][ch] = True
                    state['auto_answered'][ch] = True
                    state['answers'][ch] = None
            state['processing'] = True
            state['timer_running'] = False
            await self.set_state(self.code, state)
            asyncio.create_task(self.process_answers())

    async def process_answers(self):
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if not state or state.get('processed'):
                return

            state['processed'] = True
            state['processing'] = False
            await self.set_state(self.code, state)

            q = state.get('question')
            if not q:
                return
            correct = q.get('correct')

            results_by_label = {}
            results_by_channel = {}
            snapshot = state.get('player_label_snapshot', {})

            for pl in ('player1', 'player2'):
                ch = snapshot.get(pl)
                ans = state['answers'].get(ch) if ch else None
                timed_out = state['auto_answered'].get(ch, False) if ch else True
                is_correct = (ans == correct and not timed_out and correct is not None)

                if is_correct and ch:
                    state['scores'][pl] = state['scores'].get(pl, 0) + 1

                res = {'your_answer': ans, 'is_correct': is_correct, 'timed_out': timed_out}
                results_by_label[pl] = res
                if ch:
                    results_by_channel[ch] = res

            state['last_results_by_label'] = {
                'results': results_by_label,
                'correct_answer': correct,
                'scores': dict(state['scores']),
                'question_num': state['question_num']
            }
            state['last_results_ack'] = []
            state['question_num'] += 1
            await self.set_state(self.code, state)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'show.result',
                    'results_by_label': results_by_label,
                    'results_by_channel': results_by_channel,
                    'correct_answer': correct,
                    'scores': state['scores'],
                    'question_num': state['question_num'] - 1
                }
            )

        await asyncio.sleep(3)
        await self.send_next_question()

    async def show_result(self, event):
        results_by_channel = event.get('results_by_channel', {})
        results_by_label = event.get('results_by_label', {})
        correct_answer = event.get('correct_answer')
        scores = event.get('scores')
        question_num = event.get('question_num')

        base_payload = {
            'type': 'result',
            'scores': scores,
            'question_num': question_num,
            'correct_answer': correct_answer
        }

        sent = False
        player_label = None

        r = results_by_channel.get(self.channel_name)
        if r:
            msg = (f"Time up! Correct: {correct_answer}" if r.get('timed_out')
                   else f"Your answer: {r.get('your_answer')} {'✓' if r.get('is_correct') else '✗'}")
            await self.send(json.dumps({**base_payload, 'message': msg}))
            sent = True

        if not sent:
            try:
                lock = await self.get_redis_lock(self.code)
                async with lock:
                    state = await self.get_state(self.code)
                    if state:
                        player_label = state['channel_to_player'].get(self.channel_name)
                        if not player_label:
                            snapshot = state.get('player_label_snapshot', {})
                            player_label = next((pl for pl, ch in snapshot.items() if ch == self.channel_name), None)

                        if player_label and player_label in results_by_label:
                            r2 = results_by_label[player_label]
                            msg = (f"Time up! Correct: {correct_answer}" if r2.get('timed_out')
                                   else f"Your answer: {r2.get('your_answer')} {'✓' if r2.get('is_correct') else '✗'}")
                            await self.send(json.dumps({**base_payload, 'message': msg}))
                            sent = True
            except Exception as e:
                logger.error(f"Label lookup error: {e}")

        if not sent:
            await self.send(json.dumps({**base_payload, 'message': 'Kết quả đã cập nhật'}))

        if player_label:
            try:
                lock = await self.get_redis_lock(self.code)
                async with lock:
                    state = await self.get_state(self.code)
                    if state:
                        ack = set(state.get('last_results_ack', []))
                        ack.add(player_label)
                        state['last_results_ack'] = list(ack)
                        await self.set_state(self.code, state)
            except Exception as e:
                logger.error(f"Ack failed: {e}")

    async def start_quiz(self, event):
        await self.send(json.dumps({
            'type': 'start',
            'question': event['question'],
            'question_num': event['question_num'],
            'timer': event['timer']
        }))

    async def match_finished(self, event):
        await self.send(json.dumps({'type': 'finished', 'scores': event.get('scores')}))

    async def player_answered(self, event):
        await self.send(json.dumps({'type': 'player_answered', 'player_label': event['player_label']}))

    async def player_joined(self, event):
        await self.send(json.dumps({'type': 'player_joined', 'player_label': event['player_label']}))