import type { Schemas } from "$lib/api/client";
import { tnp, tp } from "$lib/locale";

export function outcome(said: Schemas["Outcome"]): string {
  switch (said) {
    case "valid":
      return tp("outcome", "valid");
    case "completed":
      return tp("outcome", "completed");
    case "salvaged":
      return tp("outcome", "salvaged");
    case "invalid":
      return tp("outcome", "invalid");
    case "errored":
      return tp("outcome", "errored");
    case "unread":
      return tp("outcome", "unread");
    case "stopped":
      return tp("outcome", "stopped");
  }
}

export function outcomes(said: Schemas["Outcome"], n: number): string {
  const given = { num: n };
  switch (said) {
    case "valid":
      return tnp("outcome", "%(num)s valid", "%(num)s valid", n, given);
    case "completed":
      return tnp("outcome", "%(num)s completed", "%(num)s completed", n, given);
    case "salvaged":
      return tnp("outcome", "%(num)s salvaged", "%(num)s salvaged", n, given);
    case "invalid":
      return tnp("outcome", "%(num)s invalid", "%(num)s invalid", n, given);
    case "errored":
      return tnp("outcome", "%(num)s errored", "%(num)s errored", n, given);
    case "unread":
      return tnp("outcome", "%(num)s unread", "%(num)s unread", n, given);
    case "stopped":
      return tnp("outcome", "%(num)s stopped", "%(num)s stopped", n, given);
  }
}
