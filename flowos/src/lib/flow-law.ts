import { FlowContext, FlowLawResult, FlowLawViolation, FlowParticleSnapshot } from '../types';

export class FlowLaw {
  private readonly maxDraftParticles: number;

  constructor(maxDraftParticles: number = 10) {
    this.maxDraftParticles = maxDraftParticles;
  }

  evaluate(particles: FlowParticleSnapshot[], context?: FlowContext): FlowLawResult {
    const violations: FlowLawViolation[] = [];

    const uncollapsed = particles.filter((particle) => particle.latest.status === 'draft');
    if (uncollapsed.length > this.maxDraftParticles) {
      violations.push({
        code: 'PARTICLE_OVERFLOW',
        message: 'Too many draft particles without collapse',
        context,
      });
    }

    const orphaned = particles.filter((particle) => !particle.latest.context.persona);
    if (orphaned.length) {
      violations.push({
        code: 'ORPHANED_PARTICLE',
        message: 'Particles should reference a persona to maintain narrative consistency',
        context,
      });
    }

    return { passed: violations.length === 0, violations };
  }
}
