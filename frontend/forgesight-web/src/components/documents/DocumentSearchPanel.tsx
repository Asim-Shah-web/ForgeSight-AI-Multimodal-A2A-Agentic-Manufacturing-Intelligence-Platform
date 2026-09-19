import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { searchDocuments } from '@/api/endpoints/documents';
import { Button } from '@/components/ui/Button';
import { ErrorBanner } from '@/components/ui/ErrorBanner';
import { EmptyState } from '@/components/ui/EmptyState';
import { Card } from '@/components/ui/Card';

export function DocumentSearchPanel() {
  const [query, setQuery] = useState('');
  const mutation = useMutation({ mutationFn: (q: string) => searchDocuments(q) });

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;
    mutation.mutate(query);
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="mb-3 flex gap-2">
        <input
          aria-label="Search technical SOPs"
          placeholder="e.g. placement tolerance for C17"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button type="submit" isLoading={mutation.isPending}>
          Search SOPs
        </Button>
      </form>

      {mutation.isError && <ErrorBanner error={mutation.error} />}

      {mutation.isSuccess && mutation.data.no_relevant_document_found && (
        <EmptyState
          title="No relevant SOP found for this query"
          description="Try rephrasing, or broadening the search terms."
        />
      )}

      {mutation.isSuccess && !mutation.data.no_relevant_document_found && (
        <div className="space-y-2">
          {mutation.data.passages.map((passage) => (
            <Card key={passage.passage_id}>
              <p className="font-medium">{passage.document_title}</p>
              <p className="text-xs text-slate-500">
                {passage.section_reference} · score {passage.retrieval_score.toFixed(2)}
              </p>
              <p className="mt-2 text-sm text-slate-700">{passage.chunk_text}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}