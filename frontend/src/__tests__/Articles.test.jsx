import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Articles from '../pages/Articles';

const mockArticles = [
  {
    id: 1,
    title: 'Test Article 1',
    authors: 'Author One',
    abstract: 'This is the abstract for test article 1',
    source: 'arxiv',
    source_name: 'arXiv',
    url: 'https://example.com/1',
    is_read: false,
    rating: null,
    published_date: '2024-01-15',
    citation_count: 10,
  },
  {
    id: 2,
    title: 'Test Article 2',
    authors: 'Author Two',
    abstract: 'This is the abstract for test article 2',
    source: 'semanticscholar',
    source_name: 'Semantic Scholar',
    url: 'https://example.com/2',
    is_read: true,
    rating: 4,
    published_date: '2024-01-10',
    citation_count: 25,
  },
];

const mockSources = [
  { source_name: 'arXiv', count: 100 },
  { source_name: 'Semantic Scholar', count: 50 },
];

const mockCategories = [
  { code: 'cs.AI', name: 'Artificial Intelligence' },
  { code: 'cs.LG', name: 'Machine Learning' },
];

describe('Articles', () => {
  beforeEach(() => {
    fetch.mockImplementation((url) => {
      if (url.includes('/articles/sources')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSources),
        });
      }
      if (url.includes('/fetch/arxiv/categories')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockCategories),
        });
      }
      if (url.includes('/articles?') || url.includes('/articles')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            articles: mockArticles,
            total: 2,
          }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  it('renders loading state initially', () => {
    render(<Articles />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders articles after loading', async () => {
    render(<Articles />);

    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
      expect(screen.getByText('Test Article 2')).toBeInTheDocument();
    });
  });

  it('displays article metadata correctly', async () => {
    render(<Articles />);

    await waitFor(() => {
      expect(screen.getByText('Author One')).toBeInTheDocument();
      expect(screen.getByText('Author Two')).toBeInTheDocument();
      expect(screen.getByText('10 citations')).toBeInTheDocument();
      expect(screen.getByText('25 citations')).toBeInTheDocument();
    });
  });

  it('shows read status correctly', async () => {
    render(<Articles />);

    await waitFor(() => {
      const markReadButtons = screen.getAllByRole('button', { name: /mark read/i });
      const readButtons = screen.getAllByRole('button', { name: /^read$/i });

      expect(markReadButtons.length).toBe(1); // One unread article
      expect(readButtons.length).toBe(1); // One read article
    });
  });

  it('displays total article count', async () => {
    render(<Articles />);

    await waitFor(() => {
      expect(screen.getByText('2 total')).toBeInTheDocument();
    });
  });

  it('renders filter controls', async () => {
    render(<Articles />);

    await waitFor(() => {
      expect(screen.getByText('Unread only')).toBeInTheDocument();
    });
  });

  it('renders fetch buttons', async () => {
    render(<Articles />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /fetch arxiv/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /fetch semantic scholar/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /process articles/i })).toBeInTheDocument();
    });
  });

  it('toggles unread filter', async () => {
    render(<Articles />);

    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });

    const unreadSwitch = screen.getByRole('checkbox', { name: /unread only/i });
    fireEvent.click(unreadSwitch);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('unread_only=true')
      );
    });
  });

  it('opens arXiv fetch dialog', async () => {
    render(<Articles />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /fetch arxiv/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /fetch arxiv/i }));

    await waitFor(() => {
      expect(screen.getByText('Fetch from arXiv')).toBeInTheDocument();
      expect(screen.getByLabelText('Search Query')).toBeInTheDocument();
    });
  });

  it('opens Semantic Scholar fetch dialog', async () => {
    render(<Articles />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /fetch semantic scholar/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /fetch semantic scholar/i }));

    await waitFor(() => {
      expect(screen.getByText('Fetch from Semantic Scholar')).toBeInTheDocument();
    });
  });

  it('marks article as read', async () => {
    fetch.mockImplementation((url, options) => {
      if (url.includes('/read') && options?.method === 'POST') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ success: true }),
        });
      }
      if (url.includes('/articles/sources')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockSources),
        });
      }
      if (url.includes('/fetch/arxiv/categories')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockCategories),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          articles: mockArticles,
          total: 2,
        }),
      });
    });

    render(<Articles />);

    await waitFor(() => {
      expect(screen.getByText('Test Article 1')).toBeInTheDocument();
    });

    const markReadButton = screen.getByRole('button', { name: /mark read/i });
    fireEvent.click(markReadButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/articles/1/read'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ is_read: true }),
        })
      );
    });
  });
});
