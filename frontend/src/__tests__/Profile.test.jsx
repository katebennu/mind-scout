import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Profile from '../pages/Profile';

const mockProfile = {
  interests: ['machine learning', 'NLP'],
  skill_level: 'intermediate',
  preferred_sources: ['arxiv', 'semanticscholar'],
  daily_reading_goal: 5,
};

const mockStats = {
  total_articles: 100,
  read_articles: 45,
  read_percentage: 45,
  rated_articles: 30,
  average_rating: 4.2,
  articles_by_source: {
    arXiv: 60,
    'Semantic Scholar': 40,
  },
};

describe('Profile', () => {
  beforeEach(() => {
    fetch.mockImplementation((url) => {
      if (url.includes('/profile/stats')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockStats),
        });
      }
      if (url.includes('/profile')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockProfile),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  it('renders loading state initially', () => {
    render(<Profile />);
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('renders profile data after loading', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByText('Profile & Settings')).toBeInTheDocument();
      expect(screen.getByText('machine learning')).toBeInTheDocument();
      expect(screen.getByText('NLP')).toBeInTheDocument();
    });
  });

  it('displays skill level', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByText('intermediate')).toBeInTheDocument();
    });
  });

  it('displays preferred sources', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByText('arxiv, semanticscholar')).toBeInTheDocument();
    });
  });

  it('displays daily reading goal', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByText('5 papers')).toBeInTheDocument();
    });
  });

  it('displays statistics', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument(); // total articles
      expect(screen.getByText('45')).toBeInTheDocument(); // read articles
      expect(screen.getByText('30')).toBeInTheDocument(); // rated articles
    });
  });

  it('displays average rating', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByText(/4\.2/)).toBeInTheDocument();
    });
  });

  it('displays articles by source breakdown', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByText('arXiv')).toBeInTheDocument();
      expect(screen.getByText('60')).toBeInTheDocument();
      expect(screen.getByText('Semantic Scholar')).toBeInTheDocument();
      expect(screen.getByText('40')).toBeInTheDocument();
    });
  });

  it('shows edit button', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
    });
  });

  it('enters edit mode when edit button is clicked', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
    });
  });

  it('shows save button in edit mode', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
    });
  });

  it('cancels edit and restores original values', async () => {
    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /cancel/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /cancel/i })).not.toBeInTheDocument();
    });
  });

  it('saves profile changes', async () => {
    fetch.mockImplementation((url, options) => {
      if (url.includes('/profile') && options?.method === 'PUT') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockProfile),
        });
      }
      if (url.includes('/profile/stats')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockStats),
        });
      }
      if (url.includes('/profile')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockProfile),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });

    render(<Profile />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/profile'),
        expect.objectContaining({
          method: 'PUT',
        })
      );
    });
  });
});
