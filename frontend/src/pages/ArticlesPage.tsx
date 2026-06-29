/*
 * Description: Article data entry and list page.
 *
 * Author: qinzhenya
 * Created: 2026-06-29
 */

import { useEffect, useState, type FormEvent } from "react";
import { api, type Article } from "@/api/client";
import { cn } from "@/lib/utils";

export function ArticlesPage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    try {
      setArticles(await api.listArticles());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await api.createArticle({ title, body });
      setTitle("");
      setBody("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create");
    }
  }

  return (
    <main className={cn("mx-auto flex max-w-2xl flex-col", "p-6")}>
      <h1 className="text-2xl font-semibold">Articles</h1>

      <form onSubmit={handleSubmit} className={cn("flex flex-col", "mt-4 gap-2")}>
        <input
          className={cn("rounded border", "p-2")}
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <textarea
          className={cn("rounded border", "p-2")}
          placeholder="Body"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
        <button
          className={cn("rounded", "p-2", "bg-primary text-primary-foreground")}
          type="submit"
        >
          Create
        </button>
      </form>

      {error && <p className="mt-4 text-destructive">{error}</p>}

      {loading && <p className="mt-6 text-muted-foreground">Loading...</p>}
      {!loading && !error && articles.length === 0 && (
        <p className="mt-6 text-muted-foreground">No articles yet.</p>
      )}

      <ul className={cn("flex flex-col", "mt-6 gap-2")}>
        {articles.map((article) => (
          <li key={article.id} className={cn("rounded border", "p-3")}>
            <p className="font-medium">{article.title}</p>
            <p className="text-sm text-muted-foreground">{article.body}</p>
          </li>
        ))}
      </ul>
    </main>
  );
}
