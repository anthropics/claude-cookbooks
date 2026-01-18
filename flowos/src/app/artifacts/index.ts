import { ArtifactRecord, ArtifactVersion } from '../../types';
import { MemoryStorage } from '../../storage';
import { now, randomId } from '../../utils';

export class ArtifactVault {
  constructor(private readonly storage: MemoryStorage) {}

  registerArtifact(project: string, name: string, description?: string): ArtifactRecord {
    const record: ArtifactRecord = {
      id: randomId(),
      project,
      name,
      description,
      versions: [],
    };
    return this.storage.upsertArtifact(record);
  }

  addVersion(artifactId: string, version: string, metadata?: Record<string, unknown>): ArtifactRecord {
    const existing = this.storage.getArtifact(artifactId);
    if (!existing) {
      throw new Error(`Artifact ${artifactId} not found`);
    }
    const versionEntry: ArtifactVersion = {
      id: randomId(),
      artifact: artifactId,
      version,
      createdAt: now(),
      metadata,
    };
    const updated: ArtifactRecord = { ...existing, versions: [...existing.versions, versionEntry] };
    return this.storage.upsertArtifact(updated);
  }

  listArtifacts(): ArtifactRecord[] {
    return this.storage.listArtifacts();
  }
}
