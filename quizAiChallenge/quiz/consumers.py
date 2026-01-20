import json
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Question
from accounts.models import User
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
            state.setdefault('channel_to_user', {})
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
    def get_room(self, code):
        return Room.objects.get(code=code)

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(id=user_id)

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
    
    @database_sync_to_async
    def get_total_max_score(self, num_questions=10):
        """Calculate maximum possible score for quiz"""
        from django.db.models import Sum
        qs = Question.objects.all()[:num_questions]
        total = qs.aggregate(total=Sum('score'))['total'] or 0
        return total

    async def connect(self):
        # Kiểm tra authentication
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user = user
        self.user_id = user.id
        self.username = user.username
        
        self.code = self.scope['url_route']['kwargs']['code']
        self.room_group_name = f'quiz_{self.code}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        try:
            room = await self.get_room(self.code)
        except Exception:
            await self.send(json.dumps({'type': 'no_room'}))
            await self.close()
            return

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
                    'user_snapshot': {},
                    'answers': {},
                    'answered_flags': {},
                    'auto_answered': {},
                    'channel_to_user': {},
                    'scores': {},
                    'timer_running': False,
                    'processing': False,
                    'processed': False,
                    'expected_players': 2,
                    'last_results_by_user': None,
                    'last_results_ack': [],
                }

            # Kiểm tra user đã tồn tại chưa
            existing_users = set(state['channel_to_user'].values())
            if self.user_id in existing_users:
                await self.send(json.dumps({'type': 'error', 'message': 'Bạn đã tham gia phòng này rồi'}))
                await self.close()
                return

            # Kiểm tra phòng đầy chưa
            if len(existing_users) >= 2:
                await self.send(json.dumps({'type': 'error', 'message': 'Room full'}))
                await self.close()
                return

            state['channel_to_user'][self.channel_name] = self.user_id
            
            # Khởi tạo score cho user nếu chưa có - sử dụng string key
            if str(self.user_id) not in state['scores']:
                state['scores'][str(self.user_id)] = 0

            await self.set_state(self.code, state)

        room = await self.increment_player_count(self.code)

        # Get list of other players already in room
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            other_players = []
            if state:
                for ch, uid in state['channel_to_user'].items():
                    if uid != self.user_id:
                        try:
                            other_user = await self.get_user(uid)
                            other_players.append({
                                'user_id': uid,
                                'username': other_user.username
                            })
                        except:
                            pass

        await self.send(json.dumps({
            'type': 'joined',
            'user_id': self.user_id,
            'username': self.username,
            'player_count': room.player_count,
            'other_players': other_players,
        }))

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player.joined', 
                'user_id': self.user_id,
                'username': self.username
            }
        )

        # Resend last result on reconnect
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if state and state.get('last_results_by_user'):
                last = state['last_results_by_user']
                ack = set(state.get('last_results_ack', []))
                if str(self.user_id) not in ack:
                    res = last['results'].get(str(self.user_id), {})
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
            if (state and len(state['channel_to_user']) == 2 and state.get('question') is None
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
            state['channel_to_user'].pop(self.channel_name, None)
            
            if not state.get('channel_to_user'):
                await self.set_state(self.code, state)
                await self.delete_state(self.code)
                await self.mark_room_stopped(self.code)
            else:
                await self.set_state(self.code, state)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get('type') != 'answer':
            return

        lock = await self.get_redis_lock(self.code)
        should_stop_timer = False
        should_process = False
        
        async with lock:
            state = await self.get_state(self.code)
            if not state:
                return

            # Player already answered or not in active list
            if (self.channel_name not in state.get('active_players', [])
                or state['answered_flags'].get(self.channel_name)):
                return

            state['answered_flags'][self.channel_name] = True
            state['answers'][self.channel_name] = data['answer']
            state['auto_answered'][self.channel_name] = False

            answered_count = sum(1 for ch in state['active_players'] 
                               if state['answered_flags'].get(ch, False))

            logger.info(f"Player answered: {answered_count}/{state.get('expected_players', 2)} answered for room {self.code}")

            # LAST ANSWER → Immediately stop timer and broadcast
            if answered_count == state.get('expected_players', 2):
                if state.get('timer_running'):
                    state['timer_running'] = False
                    should_stop_timer = True
                    logger.info(f"All players answered, stopping timer for room {self.code}")

                # Then process results (after broadcast)
                if not state.get('processing') and not state.get('processed'):
                    state['processing'] = True
                    should_process = True

            await self.set_state(self.code, state)

        # Broadcasts OUTSIDE the lock to avoid deadlocks
        # 1. Tell all players to stop timer
        if should_stop_timer:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'stop_timer',
                    'reason': 'all_answered'
                }
            )

        # 2. Notify others that this player has answered
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'player.answered', 
                'user_id': self.user_id,
                'username': self.username
            }
        )

        # 3. Process answers if all players answered
        if should_process:
            asyncio.create_task(self.process_answers())

    async def send_next_question(self):
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if not state:
                return
                
            if state['question_num'] > 10:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'finished', 'scores': state['scores']}
                )
                await self.delete_state(self.code)
                await self.mark_room_stopped(self.code)
                return

            q = await self.get_random_unused_question(state['used_questions'])
            if not q:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'finished', 'scores': state['scores']}
                )
                await self.delete_state(self.code)
                await self.mark_room_stopped(self.code)
                return

            state['question'] = {
                'id': q.id, 
                'correct': getattr(q, 'correct', None),
                'score': getattr(q, 'score', 0),
                'explanation': getattr(q, 'explanation', '')
            }
            state['used_questions'].append(q.id)
            state['active_players'] = list(state['channel_to_user'].keys())

            # Snapshot user_id và username
            snapshot = {}
            for ch, user_id in state['channel_to_user'].items():
                try:
                    user = await self.get_user(user_id)
                    snapshot[str(user_id)] = {
                        'channel': ch,
                        'username': user.username
                    }
                except Exception as e:
                    logger.error(f"Snapshot error for user {user_id}: {e}")
                    pass
            state['user_snapshot'] = snapshot
            logger.info(f"Snapshot created with {len(snapshot)} users: {list(snapshot.keys())}")

            state['answers'] = {ch: None for ch in state['active_players']}
            state['answered_flags'] = {ch: False for ch in state['active_players']}
            state['auto_answered'] = {ch: False for ch in state['active_players']}
            state['processed'] = False
            state['processing'] = False
            state['timer_running'] = True

            question_payload = q.as_dict() if hasattr(q, 'as_dict') else {
                'text': q.text, 
                'a': q.a, 
                'b': q.b, 
                'c': q.c, 
                'd': q.d,
                'score': getattr(q, 'score', 0),
                'explanation': getattr(q, 'explanation', '')
            }

            await self.set_state(self.code, state)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'start',
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
                logger.info(f"Timer already stopped for room {self.code}")
                return

            logger.info(f"Timer expired for room {self.code}, auto-answering remaining players")
            # Only auto-answer if still not answered
            for ch in state['active_players']:
                if not state['answered_flags'].get(ch, False):
                    state['answered_flags'][ch] = True
                    state['auto_answered'][ch] = True
                    state['answers'][ch] = None

            # Count how many have answered after auto-answering
            answered_count = sum(1 for ch in state['active_players'] 
                               if state['answered_flags'].get(ch, False))
            
            logger.info(f"After timeout: {answered_count}/{state.get('expected_players', 2)} answered")
            
            # Stop timer and process if all answered
            state['timer_running'] = False
            
            if answered_count == state.get('expected_players', 2):
                if not state.get('processing') and not state.get('processed'):
                    state['processing'] = True
                    await self.set_state(self.code, state)
                    asyncio.create_task(self.process_answers())
                else:
                    await self.set_state(self.code, state)
            else:
                # This shouldn't happen in a 2-player game, but handle it
                await self.set_state(self.code, state)

    async def process_answers(self):
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if not state or state.get('processed'):
                return

            state['processed'] = True
            state['processing'] = False

            q = state.get('question')
            if not q:
                await self.set_state(self.code, state)
                return
            correct = q.get('correct')
            question_score = q.get('score', 0)
            explanation = q.get('explanation', '')

            results_by_user = {}
            results_by_channel = {}
            snapshot = state.get('user_snapshot', {})

            for user_id_str, user_data in snapshot.items():
                ch = user_data.get('channel')
                username = user_data.get('username')

                ans = state['answers'].get(ch)
                timed_out = state['auto_answered'].get(ch, False)
                is_correct = (ans == correct and not timed_out and correct is not None)

                points_earned = 0
                if is_correct:
                    points_earned = question_score
                    state['scores'][user_id_str] = state['scores'].get(user_id_str, 0) + points_earned

                res = {
                    'your_answer': ans,
                    'is_correct': is_correct,
                    'timed_out': timed_out,
                    'username': username,
                    'points_earned': points_earned,
                    'explanation': explanation if not is_correct else None
                }
                results_by_user[user_id_str] = res
                if ch:
                    results_by_channel[ch] = res

            state['last_results_by_user'] = {
                'results': results_by_user,
                'correct_answer': correct,
                'scores': dict(state['scores']),
                'question_num': state['question_num'],
                'explanation': explanation
            }
            state['last_results_ack'] = []
            state['question_num'] += 1
            await self.set_state(self.code, state)

        # Send result outside lock
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'show.result',
                'results_by_user': results_by_user,
                'results_by_channel': results_by_channel,
                'correct_answer': correct,
                'explanation': explanation,
                'scores': state['scores'],
                'question_num': state['question_num'] - 1
            }
        )
        
        # Also send stop_timer to ensure all clients stop their timers
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'stop_timer',
                'reason': 'results_shown'
            }
        )
        
        # Wait for player to read explanation and results (5 seconds)
        logger.info(f"Waiting for players to read results for room {self.code}")
        await asyncio.sleep(5)
        
        await self.send_next_question()

    async def show_result(self, event):
        results_by_channel = event.get('results_by_channel', {})
        results_by_user = event.get('results_by_user', {})
        correct_answer = event.get('correct_answer')
        explanation = event.get('explanation', '')
        scores = event.get('scores')
        question_num = event.get('question_num')

        base_payload = {
            'type': 'result',
            'scores': scores,
            'question_num': question_num,
            'correct_answer': correct_answer,
            'explanation': explanation
        }

        sent = False
        user_id = getattr(self, 'user_id', None)

        r = results_by_channel.get(self.channel_name)
        if r:
            if r.get('timed_out'):
                msg = f"Time up! Correct: {correct_answer}"
            elif r.get('is_correct'):
                msg = f"Your answer: {r.get('your_answer')} ✓ (+{r.get('points_earned', 0)} points)"
            else:
                msg = f"Your answer: {r.get('your_answer')} ✗"
            await self.send(json.dumps({**base_payload, 'message': msg}))
            sent = True

        if not sent and user_id:
            try:
                lock = await self.get_redis_lock(self.code)
                async with lock:
                    state = await self.get_state(self.code)
                    if state:
                        current_user_id = state['channel_to_user'].get(self.channel_name)
                        if not current_user_id:
                            snapshot = state.get('user_snapshot', {})
                            for uid, data in snapshot.items():
                                if data.get('channel') == self.channel_name:
                                    current_user_id = uid
                                    break

                        if current_user_id and str(current_user_id) in results_by_user:
                            r2 = results_by_user[str(current_user_id)]
                            if r2.get('timed_out'):
                                msg = f"Time up! Correct: {correct_answer}"
                            elif r2.get('is_correct'):
                                msg = f"Your answer: {r2.get('your_answer')} ✓ (+{r2.get('points_earned', 0)} points)"
                            else:
                                msg = f"Your answer: {r2.get('your_answer')} ✗"
                            await self.send(json.dumps({**base_payload, 'message': msg}))
                            sent = True
            except Exception as e:
                logger.error(f"User lookup error: {e}")

        if not sent:
            await self.send(json.dumps({**base_payload, 'message': 'Kết quả đã cập nhật'}))

        if user_id:
            try:
                lock = await self.get_redis_lock(self.code)
                async with lock:
                    state = await self.get_state(self.code)
                    if state:
                        ack = set(state.get('last_results_ack', []))
                        ack.add(str(user_id))
                        state['last_results_ack'] = list(ack)
                        await self.set_state(self.code, state)
            except Exception as e:
                logger.error(f"Ack failed: {e}")

    async def start(self, event):
        await self.send(json.dumps({
            'type': 'start',
            'question': event['question'],
            'question_num': event['question_num'],
            'timer': event['timer']
        }))

    async def finished(self, event):
        scores = event.get('scores', {})
        
        # Convert scores để gửi kèm username
        scores_with_names = {}
        for user_id, score in scores.items():
            try:
                user = await self.get_user(int(user_id))
                scores_with_names[user.username] = score
            except:
                scores_with_names[f'User {user_id}'] = score
        
        # Tính tổng điểm tối đa có thể
        total_max_score = await self.get_total_max_score()
        
        await self.send(json.dumps({
            'type': 'finished', 
            'scores': scores,
            'scores_with_names': scores_with_names,
            'total_max_score': total_max_score,
            'message': 'Quiz completed! Final scores:'
        }))

    async def player_answered(self, event):
        await self.send(json.dumps({
            'type': 'player_answered', 
            'user_id': event.get('user_id'),
            'username': event.get('username')
        }))

    async def stop_timer(self, event):
        await self.send(json.dumps({
            'type': 'stop_timer',
            'reason': event.get('reason', 'server')
        }))

    async def player_joined(self, event):
        await self.send(json.dumps({
            'type': 'player_joined', 
            'user_id': event.get('user_id'),
            'username': event.get('username')
        }))