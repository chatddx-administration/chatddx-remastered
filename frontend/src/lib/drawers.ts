// Convenience: kept per viewer, and the page works the same when storage is refused.
export function remembered(drawer: HTMLDetailsElement, page: string): void {
  const key = `${page}.${drawer.dataset.drawer ?? ""}`;
  try {
    if (localStorage.getItem(key) === "open") drawer.open = true;
  } catch {
    return;
  }
  drawer.addEventListener("toggle", () => {
    try {
      localStorage.setItem(key, drawer.open ? "open" : "closed");
    } catch {
      /* storage refused */
    }
  });
}
