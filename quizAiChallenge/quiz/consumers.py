import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Question
import redis.asyncio as redis
from redis.asyncio.lock import Lock as RedisLock

class QuizConsumer(AsyncWebsocketConsumer):
    # Redis client (shared across all consumers)
    redis_client = None
    
    @classmethod
    async def get_redis(cls):
        """Get or create Redis connection"""
        if cls.redis_client is None:
            cls.redis_client = await redis.from_url(
                'redis://localhost:6379',
                encoding='utf-8',
                decode_responses=True
            )
        return cls.redis_client

    # --- Redis State Helpers ---
    def state_key(self, code):
        """Get Redis key for room state"""
        return f'quiz:room:{code}'
    
    def lock_key(self, code):
        """Get Redis key for room lock"""
        return f'quiz:lock:{code}'
    
    async def get_state(self, code):
        """Get room state from Redis"""
        redis_conn = await self.get_redis()
        data = await redis_conn.get(self.state_key(code))
        if data:
            state = json.loads(data)
            # Convert lists back from JSON
            state.setdefault('active_players', [])
            state.setdefault('used_questions', [])
            state.setdefault('channel_to_player', {})
            state.setdefault('last_results_ack', [])
            return state
        return None
    
    async def set_state(self, code, state, ttl=3600):
        """Save room state to Redis with TTL"""
        redis_conn = await self.get_redis()
        # Convert sets to lists for JSON serialization
        state_copy = state.copy()
        if 'last_results_ack' in state_copy and isinstance(state_copy['last_results_ack'], set):
            state_copy['last_results_ack'] = list(state_copy['last_results_ack'])
        await redis_conn.setex(
            self.state_key(code),
            ttl,
            json.dumps(state_copy)
        )
    
    async def delete_state(self, code):
        """Delete room state from Redis"""
        redis_conn = await self.get_redis()
        await redis_conn.delete(self.state_key(code))
    
    async def get_redis_lock(self, code, timeout=10):
        """Get distributed lock for room"""
        redis_conn = await self.get_redis()
        return RedisLock(
            redis_conn,
            self.lock_key(code),
            timeout=timeout,
            blocking_timeout=timeout
        )

    # --- DB helpers ---
    @database_sync_to_async
    def get_room(self, code):
        return Room.objects.get(code=code)

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
        if not qs.exists():
            return Question.objects.order_by('?').first()
        return qs.order_by('?').first()

    # -------------------------
    # connect / disconnect
    # -------------------------
    async def connect(self):
        self.code = self.scope['url_route']['kwargs']['code']
        self.room_group_name = f'quiz_{self.code}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # verify room exists
        try:
            room = await self.get_room(self.code)
        except Exception:
            await self.send(json.dumps({'type': 'no_room'}))
            await self.close()
            return

        # reject join if match already started
        if room.started:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Match already started'
            }))
            await self.close()
            return

        # Use Redis lock to safely initialize/update state
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            
            # Initialize state if not exists
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
            
            # Assign player slot
            used = set(state['channel_to_player'].values())
            if 'player1' not in used:
                player = 'player1'
            elif 'player2' not in used:
                player = 'player2'
            else:
                await self.send(json.dumps({
                    'type': 'error',
                    'message': 'Room full'
                }))
                await self.close()
                return
            
            # Store mapping
            state['channel_to_player'][self.channel_name] = player
            await self.set_state(self.code, state)

        # increment DB (outside lock)
        room = await self.increment_player_count(self.code)

        await self.send(json.dumps({
            'type': 'joined',
            'player_label': player,
            'player_count': room.player_count,
        }))

        # notify group
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'player.joined', 'player_label': player}
        )

        # Send last result if exists
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if state:
                last = state.get('last_results_by_label')
                last_ack = set(state.get('last_results_ack', []))
                if last and player not in last_ack:
                    res = last.get('results', {}).get(player)
                    payload = {
                        'type': 'result',
                        'message': ("Time up! Correct: {}".format(last.get('correct_answer')) 
                                   if (res and res.get('timed_out')) 
                                   else f"Your answer: {res.get('your_answer')} {'✓' if res and res.get('is_correct') else '✗'}" 
                                   if res else 'No result'),
                        'scores': last.get('scores'),
                        'question_num': last.get('question_num')
                    }
                    try:
                        await self.send(json.dumps(payload))
                    except Exception:
                        pass
                    last_ack.add(player)
                    state['last_results_ack'] = list(last_ack)
                    await self.set_state(self.code, state)

        # start match if ready
        if room.player_count == 2:  # assuming 2 players
            await self.mark_room_started(self.code)
            await self.send_next_question()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        try:
            await self.decrement_player_count(self.code)
        except Exception:
            pass

        should_process = False
        lock = await self.get_redis_lock(self.code)
        
        async with lock:
            state = await self.get_state(self.code)
            if not state:
                return
            
            player_label = state['channel_to_player'].pop(self.channel_name, None)

            # if in active snapshot, mark as auto-answered
            if self.channel_name in state.get('active_players', []):
                state['answered_flags'][self.channel_name] = True
                state['auto_answered'][self.channel_name] = True
                state['answers'][self.channel_name] = None
                state['active_players'] = [ch for ch in state['active_players'] if ch != self.channel_name]

            # check if all answered now
            if not state.get('processing') and not state.get('processed'):
                unanswered = [ch for ch in state.get('active_players', []) 
                             if not state['answered_flags'].get(ch, False)]
                if not unanswered and any(state.get('answered_flags', {}).values()):
                    # mark processing
                    state['processing'] = True
                    state['timer_running'] = False
                    should_process = True
            
            await self.set_state(self.code, state)

            # notify group (inside lock is fine)
            if player_label:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'player.left', 'player_label': player_label}
                )

        # process outside lock
        if should_process:
            await self.process_answers()

        # cleanup if empty
        async with lock:
            state = await self.get_state(self.code)
            if state and not state['channel_to_player']:
                await self.delete_state(self.code)
                try:
                    await self.mark_room_stopped(self.code)
                except Exception:
                    pass

    # -------------------------
    # Quiz flow
    # -------------------------
    async def send_next_question(self):
        lock = await self.get_redis_lock(self.code)
        
        async with lock:
            state = await self.get_state(self.code)
            if not state:
                return

            # end condition
            if state['question_num'] > 10:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'match.finished', 'scores': state['scores']}
                )
                await self.delete_state(self.code)
                try:
                    await self.mark_room_stopped(self.code)
                except Exception:
                    pass
                return

            q = await self.get_random_unused_question(state['used_questions'])
            if q is None:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'match.finished', 'scores': state['scores'], 'reason': 'no_questions'}
                )
                await self.delete_state(self.code)
                try:
                    await self.mark_room_stopped(self.code)
                except Exception:
                    pass
                return

            state['question'] = {'id': q.id, 'correct': getattr(q, 'correct', None)}
            state['used_questions'].append(q.id)

            # snapshot players
            active_players = list(state['channel_to_player'].keys())
            state['active_players'] = active_players

            # snapshot label->channel
            plsnap = {}
            for ch, pl in state['channel_to_player'].items():
                plsnap[pl] = ch
            plsnap.setdefault('player1', None)
            plsnap.setdefault('player2', None)
            state['player_label_snapshot'] = plsnap

            state['expected_players'] = len(active_players)

            # reset per-question state
            state['answers'] = {ch: None for ch in active_players}
            state['answered_flags'] = {ch: False for ch in active_players}
            state['auto_answered'] = {ch: False for ch in active_players}
            state['processed'] = False
            state['processing'] = False
            state['timer_running'] = True

            try:
                question_payload = q.as_dict()
            except Exception:
                question_payload = {'id': q.id, 'text': getattr(q, 'text', None)}

            await self.set_state(self.code, state)

            # send to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'start.quiz',
                    'question': question_payload,
                    'question_num': state['question_num'],
                    'timer': 30,
                }
            )

        # start timer outside lock
        asyncio.create_task(self.start_timer())

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if data.get('type') != 'answer':
            return

        should_process = False
        lock = await self.get_redis_lock(self.code)
        
        async with lock:
            state = await self.get_state(self.code)
            if not state:
                return

            # already answered?
            if state['answered_flags'].get(self.channel_name):
                return

            # ignore if not in snapshot
            if self.channel_name not in state.get('active_players', []):
                return

            # record answer
            state['answered_flags'][self.channel_name] = True
            state['answers'][self.channel_name] = data.get('answer')
            state['auto_answered'][self.channel_name] = False

            # check if all answered
            expected = state.get('expected_players', 0)
            answered_count = sum(1 for ch in state.get('active_players', []) 
                               if state['answered_flags'].get(ch))
            
            if answered_count >= expected and not state.get('processing') and not state.get('processed'):
                state['processing'] = True
                state['timer_running'] = False
                should_process = True
            
            await self.set_state(self.code, state)

            # notify group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player.answered',
                    'player_label': state['channel_to_player'].get(self.channel_name)
                }
            )

        # process outside lock
        if should_process:
            await self.process_answers()

    async def start_timer(self):
        try:
            await asyncio.sleep(30)
            
            should_process = False
            lock = await self.get_redis_lock(self.code)
            
            async with lock:
                state = await self.get_state(self.code)
                if not state:
                    return
                
                # check if timer is still valid
                if not state.get('timer_running'):
                    return
                
                # only trigger if not already processing/processed
                if not state.get('processing') and not state.get('processed'):
                    # mark all unanswered as timed out
                    for ch in list(state.get('active_players', [])):
                        if not state['answered_flags'].get(ch):
                            state['answered_flags'][ch] = True
                            state['auto_answered'][ch] = True
                            state['answers'][ch] = None
                    
                    state['processing'] = True
                    state['timer_running'] = False
                    should_process = True
                    
                    await self.set_state(self.code, state)
            
            if should_process:
                await self.process_answers()
                
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"Timer error: {e}")
            return

    async def process_answers(self):
        lock = await self.get_redis_lock(self.code)
        
        async with lock:
            state = await self.get_state(self.code)
            if not state:
                return

            # double-check processed flag
            if state.get('processed'):
                state['processing'] = False
                await self.set_state(self.code, state)
                return
            
            # mark as processed immediately
            state['processed'] = True

            q = state.get('question')
            if q is None:
                state['processing'] = False
                await self.set_state(self.code, state)
                return

            correct = q.get('correct')

            results_by_label = {}
            results_by_channel = {}
            plsnap = state.get('player_label_snapshot', {})

            # build results
            for pl in ('player1', 'player2'):
                ch = plsnap.get(pl)
                if ch is None:
                    results_by_label[pl] = {
                        'your_answer': None,
                        'is_correct': False,
                        'timed_out': True
                    }
                    continue
                
                ans = state.get('answers', {}).get(ch)
                timed_out = state.get('auto_answered', {}).get(ch, False)
                is_correct = (ans == correct) and (not timed_out) and (correct is not None)
                
                if is_correct:
                    state['scores'][pl] = state['scores'].get(pl, 0) + 1
                
                results_by_label[pl] = {
                    'your_answer': ans,
                    'is_correct': is_correct,
                    'timed_out': timed_out
                }
                results_by_channel[ch] = results_by_label[pl]

            # store for reconnect
            state['last_results_by_label'] = {
                'results': results_by_label,
                'correct_answer': correct,
                'scores': dict(state['scores']),
                'question_num': state['question_num']
            }
            state['last_results_ack'] = []

            # increment question number
            state['question_num'] += 1
            state['processing'] = False
            
            await self.set_state(self.code, state)

            # debug
            try:
                print(f"[DEBUG] process_answers room={self.code} qnum={state['question_num']-1} scores={state['scores']}")
            except Exception:
                pass

            # broadcast (can be outside critical section)
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

        # delay before next question (outside lock)
        await asyncio.sleep(3)
        await self.send_next_question()

    # -------------------------
    # Group handlers
    # -------------------------
    async def show_result(self, event):
        results_by_channel = event.get('results_by_channel', {})
        results_by_label = event.get('results_by_label', {})

        # try channel lookup first
        r = results_by_channel.get(self.channel_name)
        if r:
            msg = (f"Time up! Correct: {event.get('correct_answer')}" 
                   if r['timed_out'] 
                   else f"Your answer: {r['your_answer']} {'✓' if r['is_correct'] else '✗'}")
            await self.send(json.dumps({
                'type': 'result',
                'message': msg,
                'scores': event.get('scores'),
                'question_num': event.get('question_num')
            }))
            
            # ack in Redis
            lock = await self.get_redis_lock(self.code)
            async with lock:
                state = await self.get_state(self.code)
                if state:
                    pl = state.get('channel_to_player', {}).get(self.channel_name)
                    if pl:
                        ack_set = set(state.get('last_results_ack', []))
                        ack_set.add(pl)
                        state['last_results_ack'] = list(ack_set)
                        await self.set_state(self.code, state)
            return

        # find by player label
        lock = await self.get_redis_lock(self.code)
        async with lock:
            state = await self.get_state(self.code)
            if not state:
                return
            
            player_label = state.get('channel_to_player', {}).get(self.channel_name)
            if not player_label:
                plsnap = state.get('player_label_snapshot', {})
                for pl, ch in plsnap.items():
                    if ch == self.channel_name:
                        player_label = pl
                        break

        if player_label:
            r2 = results_by_label.get(player_label)
            if r2:
                msg = (f"Time up! Correct: {event.get('correct_answer')}" 
                       if r2['timed_out'] 
                       else f"Your answer: {r2['your_answer']} {'✓' if r2['is_correct'] else '✗'}")
                await self.send(json.dumps({
                    'type': 'result',
                    'message': msg,
                    'scores': event.get('scores'),
                    'question_num': event.get('question_num')
                }))
                
                async with lock:
                    state = await self.get_state(self.code)
                    if state:
                        ack_set = set(state.get('last_results_ack', []))
                        ack_set.add(player_label)
                        state['last_results_ack'] = list(ack_set)
                        await self.set_state(self.code, state)
                return

        # fallback
        await self.send(json.dumps({
            'type': 'result',
            'message': 'Result (generic):',
            'results_by_label': results_by_label,
            'scores': event.get('scores'),
            'question_num': event.get('question_num')
        }))

    async def start_quiz(self, event):
        await self.send(json.dumps({
            'type': 'start',
            'question': event['question'],
            'question_num': event['question_num'],
            'timer': event['timer']
        }))

    async def match_finished(self, event):
        payload = {'type': 'finished', 'scores': event.get('scores')}
        if event.get('reason'):
            payload['reason'] = event.get('reason')
        await self.send(json.dumps(payload))

    async def player_answered(self, event):
        await self.send(json.dumps({
            'type': 'player_answered',
            'player_label': event['player_label']
        }))

    async def player_joined(self, event):
        await self.send(json.dumps({
            'type': 'player_joined',
            'player_label': event['player_label']
        }))

    async def player_left(self, event):
        await self.send(json.dumps({
            'type': 'player_left',
            'player_label': event['player_label']
        }))