/*
 * Description: Tailwind className merge helper (shadcn convention).
 *
 * Author: qinzhenya
 * Created: 2026-06-29
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes (shadcn convention). */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
