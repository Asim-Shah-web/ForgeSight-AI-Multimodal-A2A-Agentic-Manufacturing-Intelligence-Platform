import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DocumentSearchPanel } from '../DocumentSearchPanel';
import * as documentsApi from '@/api/endpoints/documents';

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient();
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('DocumentSearchPanel', () => {
  it('renders the explicit empty state on no_relevant_document_found, never stale results', async () => {
    vi.spyOn(documentsApi, 'searchDocuments').mockResolvedValue({
      passages: [],
      no_relevant_document_found: true,
      result_count: 0,
    });

    renderWithClient(<DocumentSearchPanel />);
    await userEvent.type(screen.getByLabelText('Search technical SOPs'), 'unrelated nonsense query');
    await userEvent.click(screen.getByText('Search SOPs'));

    await waitFor(() => {
      expect(screen.getByText('No relevant SOP found for this query')).toBeInTheDocument();
    });
  });
});