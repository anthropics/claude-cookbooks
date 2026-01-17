import { FlowEvent, FlowContext, MerkleLink } from '../../types';
import { hashPayload } from '../../utils';

const DEFAULT_TRACE_LIMIT = 10;

export class MerkleChain {
  private links: MerkleLink[] = [];

  private computeHash(event: FlowEvent, context: FlowContext, parent?: string): string {
    const payload = { event, context, parent };
    return hashPayload(payload);
  }

  append(event: FlowEvent, context: FlowContext): MerkleLink {
    const parent = this.links.length ? this.links[this.links.length - 1].hash : undefined;
    const hash = this.computeHash(event, context, parent);
    const link: MerkleLink = { hash, parent, context, event, createdAt: Date.now() };
    this.links.push(link);
    return link;
  }

  verify(): boolean {
    for (let i = 0; i < this.links.length; i += 1) {
      const link = this.links[i];
      const expectedHash = this.computeHash(link.event, link.context, link.parent);

      if (expectedHash !== link.hash) {
        return false;
      }
      if (i > 0 && this.links[i - 1].hash !== link.parent) {
        return false;
      }
    }
    return true;
  }

  trace(limit = DEFAULT_TRACE_LIMIT): MerkleLink[] {
    return this.links.slice(-limit);
  }

  digest(): string {
    if (!this.links.length) return hashPayload({});
    return this.links[this.links.length - 1].hash;
  }
}
