// Remove unused React import
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import 'reactflow/dist/style.css';
import './App.css';

// Components - Use the new superior Claude Squad App
import ClaudeSquadApp from './components/ClaudeSquadApp';

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
      <ClaudeSquadApp />
    </QueryClientProvider>
  );
}

export default App;