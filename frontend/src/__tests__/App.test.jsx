import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';

// Mock child components to isolate App tests
jest.mock('../pages/Articles', () => () => <div data-testid="articles-page">Articles Page</div>);
jest.mock('../pages/Recommendations', () => () => <div data-testid="recommendations-page">Recommendations Page</div>);
jest.mock('../pages/Search', () => () => <div data-testid="search-page">Search Page</div>);
jest.mock('../pages/Subscriptions', () => () => <div data-testid="subscriptions-page">Subscriptions Page</div>);
jest.mock('../pages/Notifications', () => () => <div data-testid="notifications-page">Notifications Page</div>);
jest.mock('../pages/Profile', () => () => <div data-testid="profile-page">Profile Page</div>);

describe('App', () => {
  beforeEach(() => {
    fetch.mockImplementation((url) => {
      if (url.includes('/notifications/count')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ unread: 3 }),
        });
      }
      if (url.includes('/notifications')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve({}),
      });
    });
  });

  it('renders the app header', async () => {
    render(<App />);

    expect(screen.getByText('Mind Scout')).toBeInTheDocument();
    expect(screen.getByText('AI Research Assistant')).toBeInTheDocument();
  });

  it('renders navigation tabs', async () => {
    render(<App />);

    expect(screen.getByRole('tab', { name: /articles/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /recommendations/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /search/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /subscriptions/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /notifications/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /profile/i })).toBeInTheDocument();
  });

  it('shows Articles page by default', async () => {
    render(<App />);

    expect(screen.getByTestId('articles-page')).toBeInTheDocument();
  });

  it('switches to Recommendations when tab is clicked', async () => {
    render(<App />);

    const recommendationsTab = screen.getByRole('tab', { name: /recommendations/i });
    fireEvent.click(recommendationsTab);

    expect(screen.getByTestId('recommendations-page')).toBeInTheDocument();
  });

  it('switches to Profile when tab is clicked', async () => {
    render(<App />);

    const profileTab = screen.getByRole('tab', { name: /profile/i });
    fireEvent.click(profileTab);

    expect(screen.getByTestId('profile-page')).toBeInTheDocument();
  });

  it('fetches notification count on mount', async () => {
    render(<App />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/notifications/count')
      );
    });
  });

  it('displays notification badge with count', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByLabelText('3 new notifications')).toBeInTheDocument();
    });
  });

  it('opens notification menu when bell icon is clicked', async () => {
    render(<App />);

    await waitFor(() => {
      expect(screen.getByLabelText('3 new notifications')).toBeInTheDocument();
    });

    const bellButton = screen.getByLabelText('3 new notifications');
    fireEvent.click(bellButton);

    expect(screen.getByText('No new notifications')).toBeInTheDocument();
  });
});
