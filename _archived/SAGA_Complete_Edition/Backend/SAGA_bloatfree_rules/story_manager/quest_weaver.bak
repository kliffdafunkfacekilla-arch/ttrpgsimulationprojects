import random
import time

class GruntPack:
    """A cohesive unit of enemies sharing a single initiative slot."""
    def __init__(self, name: str, pack_type: str, count: int, level: int):
        self.name = name
        self.pack_type = pack_type  # Heavies, Predators, Specialists, Balancers
        self.count = count
        self.level = level
        
    def to_dict(self):
        return {
            "name": self.name,
            "pack_type": self.pack_type,
            "count": self.count,
            "level": self.level
        }

class QuestJournal:
    """Tracks active and completed quests for the player."""
    def __init__(self):
        self.active_quests = []
        self.completed_quests = []
        
    def add_quest(self, objective: str, source: str):
        self.active_quests.append({
            "objective": objective,
            "source": source,
            "timestamp": time.time(),
            "status": "active"
        })
        
    def complete_quest(self, index: int):
        if 0 <= index < len(self.active_quests):
            quest = self.active_quests.pop(index)
            quest["status"] = "completed"
            self.completed_quests.append(quest)
            
    def get_journal_summary(self) -> str:
        if not self.active_quests: return "No active quests."
        return "\n".join([f"- {q['objective']} (Source: {q['source']})" for q in self.active_quests])
        
    def to_dict(self):
        return {
            "active_quests": self.active_quests,
            "completed_quests": self.completed_quests
        }
        
    @classmethod
    def from_dict(cls, data):
        journal = cls()
        journal.active_quests = data.get("active_quests", [])
        journal.completed_quests = data.get("completed_quests", [])
        return journal

class QuestWeaver:
    """
    Manages overarching story threads and generates localized hooks based on region data and past beats.
    """
    def __init__(self):
        self.journal = QuestJournal()
        self.beat_history = []
        self.plotline_templates = [
            {"type": "The Assassination", "objective": "Eliminate the priority target.", "pack_type": "Specialists"},
            {"type": "The Escort", "objective": "Protect the asset traversing the hostile zone.", "pack_type": "Balancers"},
            {"type": "The Retrieval", "objective": "Recover the stolen artifact from the stronghold.", "pack_type": "Heavies"},
            {"type": "The Hunt", "objective": "Track down and cull the aggressive beasts.", "pack_type": "Predators"}
        ]
        
    def log_beat(self, action: str, outcome: str):
        """Records a major story beat to ensure future adaptability."""
        self.beat_history.append({"action": action, "outcome": outcome})
        if len(self.beat_history) > 10:
            self.beat_history.pop(0)

    def generate_hook_for_cell(self, cx: int, cy: int, party_level: int = 1) -> dict:
        """
        Generates an adaptive hook utilizing local coordinate data, past beats, and Plotline Templates.
        """
        # Determine theme based on history
        template = random.choice(self.plotline_templates)
        
        if len(self.beat_history) > 0:
            last_beat = self.beat_history[-1]["action"].lower()
            if "kill" in last_beat or "attack" in last_beat:
                template = {"type": "Splinter Retaliation", "objective": "A splinter faction is tracking you, seeking revenge for your recent bloodshed.", "pack_type": "Specialists"}
            elif "steal" in last_beat or "loot" in last_beat:
                template = {"type": "The Retrieval", "objective": "The original owners of your loot want it back.", "pack_type": "Heavies"}
                
        # Generate the GruntPack for this hook
        pack_size = random.randint(2, 5)
        pack = GruntPack(f"{template['type']} Squad", template['pack_type'], pack_size, party_level)
                
        hook = {
            "id": f"hook_{cx}_{cy}",
            "type": template["type"],
            "objective": template["objective"],
            "grunt_pack": pack.to_dict()
        }
            
        # Automatically add generated main hooks to the journal
        self.journal.add_quest(hook["objective"], "World Generator")
        return hook
        
    def to_dict(self):
        return {
            "journal": self.journal.to_dict(),
            "beat_history": self.beat_history
        }
        
    @classmethod
    def from_dict(cls, data):
        weaver = cls()
        weaver.beat_history = data.get("beat_history", [])
        if "journal" in data:
            weaver.journal = QuestJournal.from_dict(data["journal"])
        return weaver
