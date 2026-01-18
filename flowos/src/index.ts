import { FlowContext, FlowEvent, FlowSnapshot } from './types';
import { MemoryStorage } from './storage';
import { ParticleEngine } from './core/particles';
import { ParticleStore } from './core/particles/store';
import { MerkleChain } from './core/chains';
import { SeedRegistry } from './core/seeds';
import { PersonaRegistry } from './core/personas';
import { FlowLaw } from './lib/flow-law';
import { ConversationManager } from './app/conversations';
import { ProjectRegistry } from './app/projects';
import { ArtifactVault } from './app/artifacts';
import { MemorySystem } from './app/memory';
import { ToolRegistry } from './app/tools';
import { randomId, now } from './utils';

export class FlowOS {
  readonly storage: MemoryStorage;
  readonly particles: ParticleEngine;
  private readonly particleStore: ParticleStore;
  readonly chain: MerkleChain;
  readonly seeds: SeedRegistry;
  readonly personas: PersonaRegistry;
  readonly flowLaw: FlowLaw;
  readonly conversations: ConversationManager;
  readonly projects: ProjectRegistry;
  readonly artifacts: ArtifactVault;
  readonly memory: MemorySystem;
  readonly tools: ToolRegistry;

  constructor() {
    this.storage = new MemoryStorage();
    this.particleStore = new ParticleStore();
    this.particles = new ParticleEngine(this.particleStore);
    this.chain = new MerkleChain();
    this.seeds = new SeedRegistry();
    this.personas = new PersonaRegistry();
    this.flowLaw = new FlowLaw();
    this.conversations = new ConversationManager(this.storage);
    this.projects = new ProjectRegistry(this.storage);
    this.artifacts = new ArtifactVault(this.storage);
    this.memory = new MemorySystem(this.storage);
    this.tools = new ToolRegistry();
  }

  createContext(partial: Partial<FlowContext> = {}): FlowContext {
    return {
      id: partial.id ?? randomId(),
      createdAt: partial.createdAt ?? now(),
      ...partial,
    };
  }

  dispatch(eventType: string, payload: Record<string, unknown>, context: FlowContext): FlowEvent {
    const event: FlowEvent = { id: randomId(), type: eventType, payload, createdAt: now() };
    this.chain.append(event, context);
    return event;
  }

  enforce(context?: FlowContext) {
    return this.flowLaw.evaluate(this.particles.listParticles(), context);
  }

  snapshot(): FlowSnapshot {
    const snapshot = this.storage.snapshot();
    return {
      ...snapshot,
      particles: this.particles.listParticles(),
      seeds: this.seeds.listSeeds(),
      personas: this.personas.listPersonas(),
      seeds: this.seeds.listSeeds(),
      personas: this.personas.listPersonas(),
    };
  }
}

export * from './types';
export * from './utils';
