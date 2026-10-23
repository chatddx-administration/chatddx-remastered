import { tp } from "$lib/locale";

export function worded(word: string): string {
  switch (word) {
    case "appendix":
      return tp("kind", "appendix");
    case "canary_set":
      return tp("kind", "canary set");
    case "case":
      return tp("kind", "case");
    case "configuration":
      return tp("kind", "configuration");
    case "engine":
      return tp("kind", "engine");
    case "expectation":
      return tp("kind", "expectation");
    case "expectation_schema":
      return tp("kind", "expectation schema");
    case "facts":
      return tp("kind", "facts");
    case "few_shot":
      return tp("kind", "few shot");
    case "instructions":
      return tp("kind", "instructions");
    case "judge":
      return tp("kind", "judge");
    case "model":
      return tp("kind", "model");
    case "output":
      return tp("kind", "output");
    case "passthrough":
      return tp("kind", "passthrough");
    case "prompt":
      return tp("kind", "prompt");
    case "reasoning":
      return tp("kind", "reasoning");
    case "sampling":
      return tp("kind", "sampling");
    case "scorer":
      return tp("kind", "scorer");
    case "tool":
      return tp("kind", "tool");
    case "toolset":
      return tp("kind", "toolset");
    case "translations":
      return tp("kind", "translations");
    case "trial":
      return tp("kind", "trial");
    default:
      return word.replaceAll("_", " ");
  }
}
