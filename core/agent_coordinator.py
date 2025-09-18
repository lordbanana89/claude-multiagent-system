"""
Agent Coordination Protocol and Negotiation System
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import threading
import heapq

from core.agent_router import get_agent_router, AgentMessage, MessageType, Priority
from core.message_bus import get_message_bus
from core.persistence import get_persistence_manager

logger = logging.getLogger(__name__)


class CoordinationType(Enum):
    """Types of coordination patterns"""
    SEQUENTIAL = "sequential"      # Tasks executed in order
    PARALLEL = "parallel"          # Tasks executed simultaneously
    VOTING = "voting"             # Agents vote on decision
    AUCTION = "auction"           # Agents bid for tasks
    CONSENSUS = "consensus"       # Reach agreement
    MASTER_SLAVE = "master_slave" # One coordinator, multiple workers
    PEER_TO_PEER = "peer_to_peer" # Agents coordinate directly


class NegotiationState(Enum):
    """States of negotiation"""
    INITIATED = "initiated"
    PROPOSING = "proposing"
    NEGOTIATING = "negotiating"
    VOTING = "voting"
    AGREED = "agreed"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class CoordinationTask:
    """Task requiring coordination"""
    id: str
    type: CoordinationType
    participants: List[str]
    objective: str
    constraints: Dict[str, Any]
    deadline: float
    priority: Priority
    status: str = "pending"
    result: Optional[Dict] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class Proposal:
    """Agent proposal for task"""
    id: str
    task_id: str
    agent_id: str
    offer: Dict[str, Any]
    cost: float  # Resource cost
    confidence: float  # Confidence in completion
    estimated_time: float
    constraints: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class Agreement:
    """Coordination agreement between agents"""
    id: str
    task_id: str
    participants: List[str]
    terms: Dict[str, Any]
    assignments: Dict[str, List[str]]  # agent_id -> task assignments
    deadline: float
    penalties: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"


class ContractNet:
    """Contract Net Protocol implementation"""

    def __init__(self, coordinator: 'AgentCoordinator'):
        self.coordinator = coordinator
        self.active_contracts: Dict[str, Agreement] = {}
        self.bids: Dict[str, List[Proposal]] = defaultdict(list)

    def announce_task(self, task: CoordinationTask) -> str:
        """Announce task to potential contractors"""
        announcement = AgentMessage(
            id=str(uuid.uuid4()),
            type=MessageType.BROADCAST,
            source="coordinator",
            target="broadcast",
            content={
                'protocol': 'contract_net',
                'action': 'task_announcement',
                'task': {
                    'id': task.id,
                    'objective': task.objective,
                    'constraints': task.constraints,
                    'deadline': task.deadline
                }
            },
            priority=task.priority,
            timestamp=time.time(),
            ttl=60
        )

        self.coordinator.router.send_message(announcement)
        return announcement.id

    def submit_bid(self, proposal: Proposal):
        """Submit bid for a task"""
        self.bids[proposal.task_id].append(proposal)

    def evaluate_bids(self, task_id: str) -> Optional[Agreement]:
        """Evaluate bids and select winners"""
        if task_id not in self.bids:
            return None

        bids = self.bids[task_id]
        if not bids:
            return None

        # Score bids (higher is better)
        scored_bids = []
        for bid in bids:
            score = (bid.confidence * 0.4 +
                    (1.0 / (bid.cost + 1)) * 0.3 +
                    (1.0 / (bid.estimated_time + 1)) * 0.3)
            scored_bids.append((score, bid))

        # Sort by score
        scored_bids.sort(reverse=True)

        # Select top bids
        selected = scored_bids[:3]  # Select top 3 bidders

        # Create agreement
        agreement = Agreement(
            id=str(uuid.uuid4()),
            task_id=task_id,
            participants=[bid.agent_id for _, bid in selected],
            terms={
                'selected_bids': [bid.id for _, bid in selected],
                'total_cost': sum(bid.cost for _, bid in selected)
            },
            assignments={
                bid.agent_id: [f"subtask_{i}"]
                for i, (_, bid) in enumerate(selected)
            },
            deadline=max(bid.estimated_time for _, bid in selected)
        )

        self.active_contracts[agreement.id] = agreement
        return agreement


class VotingProtocol:
    """Distributed voting for collective decisions"""

    def __init__(self, coordinator: 'AgentCoordinator'):
        self.coordinator = coordinator
        self.active_votes: Dict[str, Dict] = {}
        self.ballots: Dict[str, Dict[str, Any]] = defaultdict(dict)

    def initiate_vote(self, topic: str, options: List[str],
                      voters: List[str], deadline: float) -> str:
        """Start a voting session"""
        vote_id = str(uuid.uuid4())

        self.active_votes[vote_id] = {
            'topic': topic,
            'options': options,
            'voters': voters,
            'deadline': deadline,
            'status': 'open'
        }

        # Send voting request
        for voter in voters:
            message = AgentMessage(
                id=str(uuid.uuid4()),
                type=MessageType.QUERY,
                source="coordinator",
                target=voter,
                content={
                    'protocol': 'voting',
                    'action': 'cast_vote',
                    'vote_id': vote_id,
                    'topic': topic,
                    'options': options,
                    'deadline': deadline
                },
                priority=Priority.HIGH,
                timestamp=time.time(),
                requires_ack=True
            )
            self.coordinator.router.send_message(message)

        return vote_id

    def cast_vote(self, vote_id: str, voter: str, choice: str, weight: float = 1.0):
        """Cast a vote"""
        if vote_id not in self.active_votes:
            logger.error(f"Unknown vote: {vote_id}")
            return

        vote = self.active_votes[vote_id]
        if vote['status'] != 'open':
            logger.error(f"Vote {vote_id} is closed")
            return

        if voter not in vote['voters']:
            logger.error(f"{voter} not authorized to vote on {vote_id}")
            return

        if choice not in vote['options']:
            logger.error(f"Invalid choice: {choice}")
            return

        self.ballots[vote_id][voter] = {
            'choice': choice,
            'weight': weight,
            'timestamp': time.time()
        }

    def tally_votes(self, vote_id: str) -> Dict[str, Any]:
        """Tally votes and determine winner"""
        if vote_id not in self.active_votes:
            return {'error': 'Unknown vote'}

        vote = self.active_votes[vote_id]
        vote['status'] = 'closed'

        ballots = self.ballots.get(vote_id, {})

        # Count votes
        results = defaultdict(float)
        for voter, ballot in ballots.items():
            results[ballot['choice']] += ballot['weight']

        # Determine winner
        if results:
            winner = max(results.items(), key=lambda x: x[1])
        else:
            winner = (None, 0)

        return {
            'vote_id': vote_id,
            'topic': vote['topic'],
            'winner': winner[0],
            'results': dict(results),
            'turnout': len(ballots) / len(vote['voters']) if vote['voters'] else 0
        }


class ConsensusProtocol:
    """Byzantine Fault Tolerant consensus protocol"""

    def __init__(self, coordinator: 'AgentCoordinator'):
        self.coordinator = coordinator
        self.consensus_rounds: Dict[str, Dict] = {}

    def propose_value(self, topic: str, value: Any, participants: List[str]) -> str:
        """Propose value for consensus"""
        consensus_id = str(uuid.uuid4())

        self.consensus_rounds[consensus_id] = {
            'topic': topic,
            'proposed_value': value,
            'participants': participants,
            'phase': 'prepare',
            'promises': {},
            'accepts': {},
            'round': 0
        }

        # Phase 1: Prepare
        for participant in participants:
            message = AgentMessage(
                id=str(uuid.uuid4()),
                type=MessageType.COORDINATION,
                source="coordinator",
                target=participant,
                content={
                    'protocol': 'consensus',
                    'phase': 'prepare',
                    'consensus_id': consensus_id,
                    'topic': topic,
                    'round': 0
                },
                priority=Priority.HIGH,
                timestamp=time.time(),
                requires_ack=True
            )
            self.coordinator.router.send_message(message)

        return consensus_id

    def handle_promise(self, consensus_id: str, agent_id: str, promise: Dict):
        """Handle promise from agent"""
        if consensus_id not in self.consensus_rounds:
            return

        round_data = self.consensus_rounds[consensus_id]
        round_data['promises'][agent_id] = promise

        # Check if we have majority
        if len(round_data['promises']) > len(round_data['participants']) / 2:
            # Phase 2: Accept
            self._start_accept_phase(consensus_id)

    def _start_accept_phase(self, consensus_id: str):
        """Start accept phase"""
        round_data = self.consensus_rounds[consensus_id]
        round_data['phase'] = 'accept'

        for participant in round_data['participants']:
            message = AgentMessage(
                id=str(uuid.uuid4()),
                type=MessageType.COORDINATION,
                source="coordinator",
                target=participant,
                content={
                    'protocol': 'consensus',
                    'phase': 'accept',
                    'consensus_id': consensus_id,
                    'value': round_data['proposed_value'],
                    'round': round_data['round']
                },
                priority=Priority.HIGH,
                timestamp=time.time(),
                requires_ack=True
            )
            self.coordinator.router.send_message(message)

    def handle_accept(self, consensus_id: str, agent_id: str, accept: bool):
        """Handle accept from agent"""
        if consensus_id not in self.consensus_rounds:
            return

        round_data = self.consensus_rounds[consensus_id]
        round_data['accepts'][agent_id] = accept

        # Check if we have majority acceptance
        accepts = sum(1 for a in round_data['accepts'].values() if a)
        if accepts > len(round_data['participants']) / 2:
            round_data['phase'] = 'committed'
            self._broadcast_decision(consensus_id, round_data['proposed_value'])

    def _broadcast_decision(self, consensus_id: str, value: Any):
        """Broadcast consensus decision"""
        round_data = self.consensus_rounds[consensus_id]

        for participant in round_data['participants']:
            message = AgentMessage(
                id=str(uuid.uuid4()),
                type=MessageType.NOTIFICATION,
                source="coordinator",
                target=participant,
                content={
                    'protocol': 'consensus',
                    'phase': 'committed',
                    'consensus_id': consensus_id,
                    'value': value
                },
                priority=Priority.HIGH,
                timestamp=time.time()
            )
            self.coordinator.router.send_message(message)


class AgentCoordinator:
    """
    Main coordination system managing agent interactions
    """

    def __init__(self):
        self.router = get_agent_router()
        self.message_bus = get_message_bus()
        self.persistence = get_persistence_manager()

        # Coordination protocols
        self.contract_net = ContractNet(self)
        self.voting = VotingProtocol(self)
        self.consensus = ConsensusProtocol(self)

        # Task management
        self.coordination_tasks: Dict[str, CoordinationTask] = {}
        self.task_queue: List[Tuple[float, CoordinationTask]] = []  # Priority queue
        self.negotiations: Dict[str, NegotiationState] = {}

        # Metrics
        self.metrics = {
            'tasks_coordinated': 0,
            'successful_negotiations': 0,
            'failed_negotiations': 0,
            'consensus_reached': 0
        }

        self._lock = threading.Lock()
        self._running = False
        self._task_processor = None

        logger.info("AgentCoordinator initialized")

    def start(self):
        """Start coordinator"""
        self._running = True
        self.router.start()

        # Start task processor
        self._task_processor = threading.Thread(target=self._process_tasks)
        self._task_processor.daemon = True
        self._task_processor.start()

        logger.info("AgentCoordinator started")

    def stop(self):
        """Stop coordinator"""
        self._running = False
        self.router.stop()

        if self._task_processor:
            self._task_processor.join(timeout=2)

        logger.info("AgentCoordinator stopped")

    def submit_coordination_task(self, task: CoordinationTask) -> str:
        """Submit task requiring coordination"""
        with self._lock:
            self.coordination_tasks[task.id] = task

            # Add to priority queue
            priority_value = -task.priority.value  # Negative for max heap
            heapq.heappush(self.task_queue, (priority_value, task))

            logger.info(f"Submitted coordination task: {task.id}")
            return task.id

    def _process_tasks(self):
        """Process coordination tasks"""
        while self._running:
            with self._lock:
                if self.task_queue:
                    _, task = heapq.heappop(self.task_queue)
                    self._coordinate_task(task)

            time.sleep(1)

    def _coordinate_task(self, task: CoordinationTask):
        """Coordinate task execution"""
        logger.info(f"Coordinating task {task.id} with type {task.type}")

        try:
            if task.type == CoordinationType.SEQUENTIAL:
                self._coordinate_sequential(task)
            elif task.type == CoordinationType.PARALLEL:
                self._coordinate_parallel(task)
            elif task.type == CoordinationType.VOTING:
                self._coordinate_voting(task)
            elif task.type == CoordinationType.AUCTION:
                self._coordinate_auction(task)
            elif task.type == CoordinationType.CONSENSUS:
                self._coordinate_consensus(task)
            elif task.type == CoordinationType.MASTER_SLAVE:
                self._coordinate_master_slave(task)
            elif task.type == CoordinationType.PEER_TO_PEER:
                self._coordinate_peer_to_peer(task)
            else:
                logger.error(f"Unknown coordination type: {task.type}")

            self.metrics['tasks_coordinated'] += 1

        except Exception as e:
            logger.error(f"Error coordinating task {task.id}: {e}")
            task.status = "failed"

    def _coordinate_sequential(self, task: CoordinationTask):
        """Sequential task coordination"""
        subtasks = task.metadata.get('subtasks', [])

        for i, subtask in enumerate(subtasks):
            agent = task.participants[i % len(task.participants)]

            message = AgentMessage(
                id=str(uuid.uuid4()),
                type=MessageType.REQUEST,
                source="coordinator",
                target=agent,
                content=subtask,
                priority=task.priority,
                timestamp=time.time(),
                correlation_id=task.id,
                requires_ack=True
            )

            self.router.send_message(message)

            # Wait for completion before next task
            time.sleep(1)  # Simplified - should wait for actual completion

        task.status = "completed"

    def _coordinate_parallel(self, task: CoordinationTask):
        """Parallel task coordination"""
        subtasks = task.metadata.get('subtasks', [])

        # Send all tasks simultaneously
        for i, subtask in enumerate(subtasks):
            agent = task.participants[i % len(task.participants)]

            message = AgentMessage(
                id=str(uuid.uuid4()),
                type=MessageType.REQUEST,
                source="coordinator",
                target=agent,
                content=subtask,
                priority=task.priority,
                timestamp=time.time(),
                correlation_id=task.id,
                requires_ack=True
            )

            self.router.send_message(message)

        task.status = "running"

    def _coordinate_voting(self, task: CoordinationTask):
        """Voting-based coordination"""
        topic = task.objective
        options = task.metadata.get('options', [])

        vote_id = self.voting.initiate_vote(
            topic=topic,
            options=options,
            voters=task.participants,
            deadline=task.deadline
        )

        task.metadata['vote_id'] = vote_id
        task.status = "voting"

    def _coordinate_auction(self, task: CoordinationTask):
        """Auction-based coordination"""
        # Use contract net protocol
        announcement_id = self.contract_net.announce_task(task)
        task.metadata['announcement_id'] = announcement_id
        task.status = "bidding"

    def _coordinate_consensus(self, task: CoordinationTask):
        """Consensus-based coordination"""
        value = task.metadata.get('proposed_value')

        consensus_id = self.consensus.propose_value(
            topic=task.objective,
            value=value,
            participants=task.participants
        )

        task.metadata['consensus_id'] = consensus_id
        task.status = "consensus"

    def _coordinate_master_slave(self, task: CoordinationTask):
        """Master-slave coordination"""
        master = task.participants[0]
        slaves = task.participants[1:]

        # Master coordinates slaves
        message = AgentMessage(
            id=str(uuid.uuid4()),
            type=MessageType.COORDINATION,
            source="coordinator",
            target=master,
            content={
                'role': 'master',
                'slaves': slaves,
                'task': task.objective,
                'constraints': task.constraints
            },
            priority=task.priority,
            timestamp=time.time(),
            correlation_id=task.id
        )

        self.router.send_message(message)
        task.status = "delegated"

    def _coordinate_peer_to_peer(self, task: CoordinationTask):
        """Peer-to-peer coordination"""
        # Agents coordinate directly
        for agent in task.participants:
            message = AgentMessage(
                id=str(uuid.uuid4()),
                type=MessageType.COORDINATION,
                source="coordinator",
                target=agent,
                content={
                    'peers': [a for a in task.participants if a != agent],
                    'task': task.objective,
                    'mode': 'peer_to_peer'
                },
                priority=task.priority,
                timestamp=time.time(),
                correlation_id=task.id
            )

            self.router.send_message(message)

        task.status = "peer_coordination"

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get coordination task status"""
        task = self.coordination_tasks.get(task_id)
        if not task:
            return None

        return {
            'id': task.id,
            'type': task.type.value,
            'status': task.status,
            'participants': task.participants,
            'result': task.result,
            'metadata': task.metadata
        }

    def get_metrics(self) -> Dict:
        """Get coordination metrics"""
        return self.metrics.copy()


# Singleton instance
_agent_coordinator = None

def get_agent_coordinator() -> AgentCoordinator:
    """Get or create coordinator instance"""
    global _agent_coordinator
    if _agent_coordinator is None:
        _agent_coordinator = AgentCoordinator()
    return _agent_coordinator