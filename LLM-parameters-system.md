# LLM Parameters System

This document describes how parameters flow through Big-AGI's LLM parameters system, from definition to API invocation.

## System Overview

The LLM parameters system operates across five layers that transform parameters from global definitions to vendor-specific API calls. Each layer serves a specific purpose in the parameter resolution pipeline.

## Parameter Flow Architecture

### Layer 1: Parameter Registry
**File**: `src/common/stores/llms/llms.parameters.ts`

The `DModelParameterRegistry` defines all available parameters with their constraints and metadata. Each parameter includes type information, validation rules, and default behavior.

**Example**: `llmVndOaiReasoningEffort4` defines a 4-value enum with 'medium' as the required fallback.

**Default Value System**: The registry supports multiple default mechanisms:
- `initialValue` - Parameter's base default (e.g., `llmVndOaiRestoreMarkdown: true`)
- `requiredFallback` - Fallback for required parameters (e.g., `llmTemperature: 0.5`)
- `nullable` - Parameters that can be explicitly null to skip API transmission

### Layer 2: Model Specifications
**File**: `src/modules/llms/server/llm.server.types.ts`

Models declare which parameters they support through `parameterSpecs` arrays. Each spec can override registry defaults:

```typescript
parameterSpecs: [
  { paramId: 'llmVndOaiReasoningEffort4' },
  { paramId: 'llmVndAntThinkingBudget', initialValue: 1024 }, // Override default
  { paramId: 'llmVndGeminiThinkingBudget', rangeOverride: [0, 8192] }, // Custom range
]
```

**Parameter Visibility**: The `hidden` flag removes parameters from the UI while keeping them functional. Models can also mark parameters as `required`.

### Layer 3: Client Configuration

The system provides two UI configurators with different scopes:

#### Full Model Configuration Dialog
**File**: `src/modules/llms/models-modal/LLMParametersEditor.tsx`
Shows all non-hidden parameters from model's `parameterSpecs`. Used in the models modal for complete configuration.

#### ChatPanel Quick Controls
**File**: `src/apps/chat/components/layout-panel/ChatPanelModelParameters.tsx`
Shows only parameters that are:
- In model's `parameterSpecs`
- Listed in `_interestingParameters` array
- Not marked as `hidden`

**Value Resolution**: Both UIs use `getAllModelParameterValues()` to merge:
1. **Fallback values** - Required parameters get their `requiredFallback` values
2. **Initial values** - Model's `initialParameters` (populated during model creation)
3. **User values** - User's `userParameters` (highest priority)

### Layer 4: AIX Translation
**File**: `src/modules/aix/client/aix.client.ts`

The AIX client transforms DLLM parameters to wire protocol format. This layer handles parameter precedence rules and name transformations:

```
// Parameter precedence: newer 4-value version takes priority over 3-value
...((llmVndOaiReasoningEffort4 || llmVndOaiReasoningEffort) ?
  { vndOaiReasoningEffort: llmVndOaiReasoningEffort4 || llmVndOaiReasoningEffort } : {})
```

**Client Options**: The system supports parameter overrides through `llmOptionsOverride` and complete replacement via `llmUserParametersReplacement`.

### Layer 5: Vendor Adaptation
**Files**: `src/modules/aix/server/dispatch/chatGenerate/adapters/*.ts`

Server-side adapters translate AIX parameters to vendor APIs. Each vendor may interpret parameters differently:

- **OpenAI**: `vndOaiReasoningEffort` → `reasoning_effort`
- **Perplexity**: Reuses OpenAI parameter format
- **OpenAI Responses API**: Maps to structured reasoning config with additional logic

## Parameter Initialization Process

When a model is loaded:

1. **Model Creation**: `modelDescriptionToDLLM()` creates the DLLM with empty `initialParameters`
2. **Initial Value Application**: `applyModelParameterInitialValues()` populates initial values from:
   - Model spec `initialValue` (highest priority)
   - Registry `initialValue` (fallback)
3. **Runtime Resolution**: `getAllModelParameterValues()` creates final parameter set:
   - Required fallbacks (for missing required parameters)
   - Initial parameters (model defaults)
   - User parameters (user overrides)

## Special Parameter Behaviors

**Hidden Parameters**: Parameters like `llmRef` are marked `hidden: true` in the registry and never appear in the UI, but remain functional for system use.

**Nullable Parameters**: Parameters with `nullable` configuration can be explicitly set to `null` to prevent transmission to the API, distinct from being undefined.

**Range Overrides**: Models can override parameter ranges (e.g., different Gemini models support different thinking budget ranges).

**Parameter Interactions**: The UI implements business logic like disabling web search when reasoning effort is 'minimal'.

## Type Safety Mechanisms

The system maintains type safety through:
- `DModelParameterId` union from registry keys
- `DModelParameterValue<T>` conditional types for values
- `DModelParameterSpec<T>` interfaces for specifications
- Runtime validation via Zod schemas at API boundaries

## Model Variant Pattern

Some vendors use model variants to enable features, for instance:
- **Anthropic**: Creates separate `idVariant: 'thinking'` entries forcing value of hidden parameters
- **Google/OpenAI**: Parameters directly on base models

## Migration and Compatibility

The architecture supports parameter evolution:
- **Version Coexistence**: Both `llmVndOaiReasoningEffort` and `llmVndOaiReasoningEffort4` exist simultaneously
- **Precedence Rules**: Newer parameters take priority during AIX translation
- **Graceful Degradation**: Unknown parameters log warnings but don't break functionality

## Key Implementation Files

- **Registry**: `src/common/stores/llms/llms.parameters.ts`
- **Specifications**: `src/modules/llms/server/llm.server.types.ts`
- **UI Controls**: `src/modules/llms/models-modal/LLMParametersEditor.tsx`
- **AIX Translation**: `src/modules/aix/client/aix.client.ts`
- **Wire Types**: `src/modules/aix/server/api/aix.wiretypes.ts`
- **Vendor Adapters**: `src/modules/aix/server/dispatch/chatGenerate/adapters/*.ts`