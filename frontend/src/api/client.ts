/*
 * Description: Minimal API client for the backend. Expand as endpoints grow.
 *
 * Author: qinzhenya
 * Created: 2026-06-29
 */

export type Article = {
  id: number;
  title: string;
  content: string;
  status: string | null;
  created_at: string;
  updated_at: string;
};

export type ArticleInput = {
  title: string;
  content?: string;
  status?: string;
};

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  // 204 No Content has no body.
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

export const api = {
  listArticles: () => request<Article[]>("/articles"),
  createArticle: (input: ArticleInput) =>
    request<Article>("/articles", { method: "POST", body: JSON.stringify(input) }),
  deleteArticle: (id: number) => request<void>(`/articles/${id}`, { method: "DELETE" }),
};
