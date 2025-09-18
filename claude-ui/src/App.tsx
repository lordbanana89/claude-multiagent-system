// Remove unused React import
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import 'reactflow/dist/style.css';
import './App.css';

// Components
import DashboardV2 from './components/DashboardV2';
// import SimpleDashboard from './components/SimpleDashboard';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: 5000, // Refetch every 5 seconds
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DashboardV2 />
    </QueryClientProvider>
  );
}

export default App;