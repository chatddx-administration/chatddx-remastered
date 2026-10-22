import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export const FIELD = "h-8 rounded-md border border-input bg-transparent px-2";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, "children"> : T;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };
