import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Question

# in-memory
room_state = {}  # as before

class QuizConsumer(AsyncWebsocketConsumer):

    # --- DB helpers (unchanged) ---
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

        # init state + per-room lock if missing
        state = room_state.setdefault(self.code, {
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
            'timer_task': None,
            'processing': False,
            'processed': False,
            'expected_players': 2,
            # extra fields
            'lock': None,  # will set below
            'last_results_by_label': None,  # store last results with question_num
            'last_results_ack': set(),       # set of player_labels who have been acked
        })
        # create lock on the event loop (safe)
        if state.get('lock') is None:
            state['lock'] = asyncio.Lock()

        # reject join if match already started (DB authoritative)
        if room.started:
            await self.send(json.dumps({
                'type': 'error',
                'message': 'Match already started'
            }))
            await self.close()
            return

        # assign player slot
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

        # store mapping
        async with state['lock']:
            state['channel_to_player'][self.channel_name] = player

        # increment DB
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

        # If there is a last result (un-acked) for this player_label, send it now
        async with state['lock']:
            last = state.get('last_results_by_label')
            if last:
                last_qnum = last.get('question_num')
                # if we haven't acked this player_label yet, send them their last result
                if player not in state.get('last_results_ack', set()):
                    # compose personal payload
                    res = last.get('results', {}).get(player)
                    payload = {
                        'type': 'result',
                        'message': ("Time up! Correct: {}".format(last.get('correct_answer')) if (res and res.get('timed_out')) else f"Your answer: {res.get('your_answer')} {'✓' if res and res.get('is_correct') else '✗'}" if res else 'No result'),
                        'scores': last.get('scores'),
                        'question_num': last_qnum
                    }
                    try:
                        await self.send(json.dumps(payload))
                    except Exception:
                        pass
                    # mark ack so we don't resend repeatedly
                    state.setdefault('last_results_ack', set()).add(player)

        # start match if ready (outside lock)
        if room.player_count == state['expected_players']:
            await self.mark_room_started(self.code)
            await self.send_next_question()

    async def disconnect(self, close_code):
        # remove from group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # decrement DB
        try:
            await self.decrement_player_count(self.code)
        except Exception:
            pass

        state = room_state.get(self.code)
        if not state:
            return

        async with state['lock']:
            player_label = state['channel_to_player'].pop(self.channel_name, None)

            # if channel was in active snapshot, mark answered as auto
            if self.channel_name in state.get('active_players', []):
                state['answered_flags'][self.channel_name] = True
                state['auto_answered'][self.channel_name] = True
                state['answers'][self.channel_name] = None
                state['active_players'] = [ch for ch in state['active_players'] if ch != self.channel_name]

            # notify group
            if player_label:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'player.left', 'player_label': player_label}
                )

            # if processing not running and all snapshot players answered -> trigger
            if not state.get('processing'):
                unanswered = [ch for ch in state.get('active_players', []) if not state['answered_flags'].get(ch, False)]
                if not unanswered and any(state.get('answered_flags', {}).values()):
                    # cancel timer
                    t = state.get('timer_task')
                    if t:
                        try:
                            t.cancel()
                        except Exception:
                            pass
                        state['timer_task'] = None
                    # call process_answers without holding lock to avoid deadlock
                    # but set processing True first
                    state['processing'] = True
                    # release lock then call process
                    pass

        # if we set processing True above, call process outside lock
        if state.get('processing'):
            await self.process_answers()

        # if no players left globally -> cleanup
        async with state['lock']:
            if not state['channel_to_player']:
                t = state.get('timer_task')
                if t:
                    try:
                        t.cancel()
                    except Exception:
                        pass
                room_state.pop(self.code, None)
                try:
                    await self.mark_room_stopped(self.code)
                except Exception:
                    pass

    # -------------------------
    # Quiz flow
    # -------------------------
    async def send_next_question(self):
        state = room_state.get(self.code)
        if not state:
            return

        async with state['lock']:
            # end condition
            if state['question_num'] > 10:
                t = state.get('timer_task')
                if t:
                    try:
                        t.cancel()
                    except Exception:
                        pass
                    state['timer_task'] = None
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'match.finished', 'scores': state['scores']}
                )
                # cleanup
                room_state.pop(self.code, None)
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
                room_state.pop(self.code, None)
                try:
                    await self.mark_room_stopped(self.code)
                except Exception:
                    pass
                return

            # set question
            state['question'] = q
            state['used_questions'].append(q.id)

            # snapshot players
            active_players = list(state['channel_to_player'].keys())
            state['active_players'] = active_players

            # snapshot label->channel at start
            plsnap = {}
            for ch, pl in state['channel_to_player'].items():
                plsnap[pl] = ch
            plsnap.setdefault('player1', None)
            plsnap.setdefault('player2', None)
            state['player_label_snapshot'] = plsnap

            state['expected_players'] = len(active_players)

            # init per-question maps
            state['answers'] = {ch: None for ch in active_players}
            state['answered_flags'] = {ch: False for ch in active_players}
            state['auto_answered'] = {ch: False for ch in active_players}
            state['processed'] = False
            state['processing'] = False

            try:
                question_payload = q.as_dict()
            except Exception:
                question_payload = {'id': q.id, 'text': getattr(q, 'text', None)}

            # cancel previous timer
            if state.get('timer_task'):
                try:
                    state['timer_task'].cancel()
                except Exception:
                    pass
                state['timer_task'] = None

            # send start to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'start.quiz',
                    'question': question_payload,
                    'question_num': state['question_num'],
                    'timer': 30,
                }
            )

            # start timer task
            state['timer_task'] = asyncio.create_task(self.start_timer())

    async def receive(self, text_data):
        data = json.loads(text_data)
        state = room_state.get(self.code)
        if not state:
            return

        if data.get('type') != 'answer':
            return

        async with state['lock']:
            # already answered?
            if state['answered_flags'].get(self.channel_name):
                return

            # ignore if not in snapshot (late join)
            if self.channel_name not in state.get('active_players', []):
                return

            # record
            state['answered_flags'][self.channel_name] = True
            state['answers'][self.channel_name] = data.get('answer')
            state['auto_answered'][self.channel_name] = False

            # notify group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player.answered',
                    'player_label': state['channel_to_player'].get(self.channel_name)
                }
            )

            # barrier check
            expected = state.get('expected_players', 0)
            answered_count = sum(1 for ch in state.get('active_players', []) if state['answered_flags'].get(ch))
            if answered_count < expected:
                return

            # set processing and cancel timer
            if state.get('processing'):
                return
            state['processing'] = True
            t = state.get('timer_task')
            if t:
                try:
                    t.cancel()
                except Exception:
                    pass
                state['timer_task'] = None

        # call processing outside lock
        await self.process_answers()

    async def start_timer(self):
        try:
            await asyncio.sleep(30)
            state = room_state.get(self.code)
            if not state:
                return
            async with state['lock']:
                if state.get('processing'):
                    return
                for ch in list(state.get('active_players', [])):
                    if not state['answered_flags'].get(ch):
                        state['answered_flags'][ch] = True
                        state['auto_answered'][ch] = True
                        state['answers'][ch] = None
                state['processing'] = True
            await self.process_answers()
        except asyncio.CancelledError:
            return
        except Exception:
            return

    async def process_answers(self):
        state = room_state.get(self.code)
        if not state:
            return

        # use lock to serialize processing
        async with state['lock']:
            if state.get('processed'):
                state['processing'] = False
                return
            state['processed'] = True

            q = state.get('question')
            if q is None:
                state['processing'] = False
                return

            try:
                correct = getattr(q, 'correct')
            except Exception:
                correct = None

            results_by_label = {}
            results_by_channel = {}  # map channel snapshot -> result (helps matching)
            plsnap = state.get('player_label_snapshot', {})

            # build results for both labels using snapshot
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

            # store last_results (for reconnect handling)
            state['last_results_by_label'] = {
                'results': results_by_label,
                'correct_answer': correct,
                'scores': dict(state['scores']),
                'question_num': state['question_num']
            }
            # clear ack set so all players can be resent on reconnect
            state['last_results_ack'] = set()

            # debug print of state (useful to trace)
            try:
                print(f"[DEBUG] process_answers room={self.code} qnum={state['question_num']} active={state['active_players']} channel_to_player={state['channel_to_player']} answers={state['answers']} flags={state['answered_flags']} scores={state['scores']}")
            except Exception:
                pass

            # broadcast event includes both maps
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'show.result',
                    'results_by_label': results_by_label,
                    'results_by_channel': results_by_channel,
                    'correct_answer': correct,
                    'scores': state['scores'],
                    'question_num': state['question_num']
                }
            )

            # increment qnum and small delay
            state['question_num'] += 1
            state['processing'] = False

        # small delay outside lock so handlers can process
        await asyncio.sleep(3)
        await self.send_next_question()

    # -------------------------
    # Group handlers
    # -------------------------
    async def show_result(self, event):
        """
        Event contains:
         - results_by_label: {player1: {...}, player2: {...}}
         - results_by_channel: {channel_name: {...}} (snapshot)
         - correct_answer, scores, question_num
        Handler tries (in order):
         1) lookup by channel_name in results_by_channel
         2) lookup by player_label via current mapping or snapshot
         3) fallback: send full results_by_label
        """
        state = room_state.get(self.code) or {}
        results_by_channel = event.get('results_by_channel', {})
        results_by_label = event.get('results_by_label', {})

        # 1) try channel lookup
        r = results_by_channel.get(self.channel_name)
        if r:
            msg = (f"Time up! Correct: {event.get('correct_answer')}" if r['timed_out'] else f"Your answer: {r['your_answer']} {'✓' if r['is_correct'] else '✗'}")
            await self.send(json.dumps({
                'type': 'result',
                'message': msg,
                'scores': event.get('scores'),
                'question_num': event.get('question_num')
            }))
            # ack if we can find player_label
            async with (state.get('lock') or asyncio.Lock()):
                pl = state.get('channel_to_player', {}).get(self.channel_name)
                if pl:
                    state.setdefault('last_results_ack', set()).add(pl)
            return

        # 2) find player_label via current mapping or snapshot
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
                msg = (f"Time up! Correct: {event.get('correct_answer')}" if r2['timed_out'] else f"Your answer: {r2['your_answer']} {'✓' if r2['is_correct'] else '✗'}")
                await self.send(json.dumps({
                    'type': 'result',
                    'message': msg,
                    'scores': event.get('scores'),
                    'question_num': event.get('question_num')
                }))
                # mark ack so reconnects won't resend
                async with (state.get('lock') or asyncio.Lock()):
                    state.setdefault('last_results_ack', set()).add(player_label)
                return

        # 3) fallback: send full results_by_label so client can show something
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
