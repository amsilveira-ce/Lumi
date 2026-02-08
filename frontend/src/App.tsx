// App.tsx - GrandCompanion Elder Care AI - Multi-mode App
import { useState } from 'react';
import { OnboardingFlow } from './components/OnboardingFlow';
import { Dashboard } from './components/Dashboard';
import { ConversationMode } from './components/ConversationMode';
import './App.css';

type AppMode = 'onboarding' | 'dashboard' | 'conversation';

function App() {
  const [mode, setMode] = useState<AppMode>('dashboard');
  const [elderProfile, setElderProfile] = useState<any>(null);

  // For development: cycle through modes
  const cycleMode = () => {
    if (mode === 'onboarding') {
      setElderProfile({
        cognitive_comfort: 'intermediate',
        personality: 'independent',
        tone_preference: 'casual'
      });
      setMode('dashboard');
    } else if (mode === 'dashboard') {
      setMode('conversation');
    } else {
      setMode('onboarding');
      setElderProfile(null);
    }
  };

  const getModeLabel = () => {
    if (mode === 'onboarding') return 'Dashboard';
    if (mode === 'dashboard') return 'Chat';
    return 'Onboarding';
  };

  return (
    <div className="App">
      {/* Development mode switcher */}
      <button
        className="dev-mode-toggle"
        onClick={cycleMode}
        style={{
          position: 'fixed',
          top: '10px',
          right: '10px',
          zIndex: 9999,
          padding: '8px 16px',
          background: '#667eea',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          fontSize: '12px',
          fontWeight: '600'
        }}
      >
        🔄 Switch to {getModeLabel()}
      </button>

      {mode === 'onboarding' && <OnboardingFlow />}
      {mode === 'dashboard' && <Dashboard />}
      {mode === 'conversation' && <ConversationMode elderProfile={elderProfile} />}
    </div>
  );
}

export default App;
