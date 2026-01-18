import { FlowSnapshot, MemoryEntry, PersonaRecord, SeedDefinition, FlowParticleSnapshot, ConversationThread, ProjectMetadata, ArtifactRecord } from '../types';
import { randomId, now } from '../utils';

type Collection<T> = Map<string, T>;

export class MemoryStorage {
  private particles: Collection<FlowParticleSnapshot> = new Map();
  private personas: Collection<PersonaRecord> = new Map();
  private seeds: Collection<SeedDefinition> = new Map();
  private conversations: Collection<ConversationThread> = new Map();
  private projects: Collection<ProjectMetadata> = new Map();
  private artifacts: Collection<ArtifactRecord> = new Map();
  private memories: Collection<MemoryEntry> = new Map();

  upsertParticle(snapshot: FlowParticleSnapshot): FlowParticleSnapshot {
    const persisted = { ...snapshot, latest: { ...snapshot.latest, updatedAt: now() } };
    this.particles.set(snapshot.id, persisted);
    return persisted;
  }

  getParticle(id: string): FlowParticleSnapshot | undefined {
    return this.particles.get(id);
  }

  listParticles(): FlowParticleSnapshot[] {
    return [...this.particles.values()];
  }

  upsertPersona(record: PersonaRecord): PersonaRecord {
    this.personas.set(record.profile.id, record);
    return record;
  }

  listPersonas(): PersonaRecord[] {
    return [...this.personas.values()];
  }

  upsertSeed(seed: SeedDefinition): SeedDefinition {
    this.seeds.set(seed.id, seed);
    return seed;
  }

  listSeeds(): SeedDefinition[] {
    return [...this.seeds.values()];
  }

  upsertConversation(thread: ConversationThread): ConversationThread {
    this.conversations.set(thread.id, thread);
    return thread;
  }

  getConversation(id: string): ConversationThread | undefined {
    return this.conversations.get(id);
  }

  listConversations(): ConversationThread[] {
    return [...this.conversations.values()];
  }

  upsertProject(project: ProjectMetadata): ProjectMetadata {
    this.projects.set(project.id, project);
    return project;
  }

  listProjects(): ProjectMetadata[] {
    return [...this.projects.values()];
  }

  upsertArtifact(record: ArtifactRecord): ArtifactRecord {
    this.artifacts.set(record.id, record);
    return record;
  }

  listArtifacts(): ArtifactRecord[] {
    return [...this.artifacts.values()];
  }

  upsertMemory(memory: MemoryEntry): MemoryEntry {
    this.memories.set(memory.id, memory);
    return memory;
  }

  listMemories(scope?: MemoryEntry['scope']): MemoryEntry[] {
    const entries = [...this.memories.values()];
    if (!scope) return entries;
    return entries.filter((entry) => entry.scope === scope);
  }

  snapshot(): FlowSnapshot {
    return {
      particles: this.listParticles(),
      personas: this.listPersonas(),
      seeds: this.listSeeds(),
      conversations: this.listConversations(),
      projects: this.listProjects(),
      artifacts: this.listArtifacts(),
      memories: this.listMemories(),
    };
  }
}
