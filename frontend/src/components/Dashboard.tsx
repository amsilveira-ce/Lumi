// Dashboard.tsx - Main home screen for GrandCompanion Elder Care AI
import { useState } from 'react';
import {
  Mic,
  Phone,
  Heart,
  Calendar,
  Clock,
  Video,
  Activity,
  Moon,
  AlertCircle,
  Users
} from 'lucide-react';
import { useUserPreferences, getPreferenceClasses } from '../hooks/useUserPreferences';
import './Dashboard.css';

export const Dashboard: React.FC = () => {
  const { contextData, isLoading, error } = useUserPreferences();
  const [isListening, setIsListening] = useState(false);
  const [emergencyTriggered, setEmergencyTriggered] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-500 mx-auto mb-4"></div>
          <p className="text-xl text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !contextData) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-red-50">
        <div className="text-center text-red-600">
          <AlertCircle className="w-16 h-16 mx-auto mb-4" />
          <p className="text-xl">{error || 'Failed to load dashboard'}</p>
        </div>
      </div>
    );
  }

  const { userProfile, preferences, dailyInsight, vitals, upcomingEvents, emergencyContacts } = contextData;
  const classes = getPreferenceClasses(preferences);

  const handleVoiceInput = () => {
    setIsListening(!isListening);
    console.log('Voice input toggled:', !isListening);
    // In production, this would trigger the Orchestrator Agent
  };

  const handleEmergency = () => {
    setEmergencyTriggered(true);
    console.log('EMERGENCY TRIGGERED - Activating Safety Agent Protocol');
    console.log('Calling emergency contacts:', emergencyContacts);
    // In production, this would trigger the Safety Agent's high-risk protocol

    // Auto-dismiss after 3 seconds for demo purposes
    setTimeout(() => {
      setEmergencyTriggered(false);
    }, 3000);
  };

  const handleHealthMonitor = () => {
    console.log('Opening Health Monitor');
    // Navigate to health details
  };

  const handleSocialFun = () => {
    console.log('Opening Social & Fun');
    // Navigate to social activities
  };

  const handleAssistant = () => {
    console.log('Opening Assistant Services');
    // Navigate to schedule/reminders
  };

  // Determine grid layout based on text size
  const gridCols = preferences.textSize === 'extra-large' ? 'grid-cols-1' : 'md:grid-cols-3 grid-cols-1';

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Emergency Alert Overlay */}
      {emergencyTriggered && (
        <div className="fixed inset-0 bg-red-600 bg-opacity-95 z-50 flex items-center justify-center animate-pulse">
          <div className="text-center text-white">
            <Phone className="w-24 h-24 mx-auto mb-6 animate-bounce" />
            <h1 className="text-5xl font-bold mb-4">CALLING FOR HELP</h1>
            <p className="text-2xl mb-2">Contacting {emergencyContacts[0]?.name}</p>
            <p className="text-xl">{emergencyContacts[0]?.phone}</p>
            <div className="mt-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-4 border-white mx-auto"></div>
            </div>
          </div>
        </div>
      )}

      {/* Main Dashboard */}
      <div className={`max-w-7xl mx-auto ${classes.container.padding}`}>
        {/* Header with Greeting & Voice Button */}
        <header className={`flex items-center justify-between mb-6 ${classes.container.padding} bg-white rounded-2xl ${classes.border} ${classes.shadow}`}>
          <div>
            <h1 className={`font-bold ${classes.text['3xl']} ${classes.textColor} mb-1`}>
              Hello, {userProfile.userName}! 👋
            </h1>
            <p className={`${classes.text.lg} text-gray-600`}>
              {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
            </p>
          </div>

          {/* Voice Input Button */}
          <button
            onClick={handleVoiceInput}
            className={`
              ${classes.button.height} ${classes.button.padding}
              ${isListening ? 'bg-red-500 animate-pulse' : 'bg-blue-500'}
              text-white rounded-full
              ${classes.shadow}
              transition-all duration-300 ease-in-out
              hover:scale-110 active:scale-95
              flex items-center gap-3
              ${preferences.contrast === 'high' ? 'border-4 border-black' : ''}
            `}
            aria-label="Voice input"
          >
            <Mic className={`${preferences.buttonSize === 'extra-large' ? 'w-10 h-10' : preferences.buttonSize === 'large' ? 'w-8 h-8' : 'w-6 h-6'}`} />
            <span className={`${classes.button.text} font-semibold`}>
              {isListening ? 'Listening...' : 'Tap to Speak'}
            </span>
          </button>
        </header>

        {/* Daily Insight Card */}
        <div className={`mb-6 ${classes.container.padding} bg-gradient-to-r from-blue-100 to-green-100 rounded-2xl ${classes.border} ${classes.shadow}`}>
          <div className="flex items-start gap-4">
            <div className={`${preferences.buttonSize === 'extra-large' ? 'text-6xl' : preferences.buttonSize === 'large' ? 'text-5xl' : 'text-4xl'}`}>
              💡
            </div>
            <div>
              <h2 className={`font-semibold ${classes.text.xl} ${classes.textColor} mb-2`}>
                Daily Insight
              </h2>
              <p className={`${classes.text.lg} ${classes.textColor}`}>
                {dailyInsight}
              </p>
            </div>
          </div>
        </div>

        {/* Emergency Button - Always Visible */}
        <div className={`mb-6`}>
          <button
            onClick={handleEmergency}
            className={`
              w-full ${classes.button.height}
              ${preferences.contrast === 'high' ? 'bg-red-600 border-4 border-black' : 'bg-red-500'}
              text-white rounded-2xl
              font-bold ${classes.button.text}
              shadow-lg
              transition-all duration-200
              hover:bg-red-600 active:scale-98
              flex items-center justify-center gap-4
            `}
            aria-label="Emergency help"
          >
            <Phone className={`${preferences.buttonSize === 'extra-large' ? 'w-10 h-10' : preferences.buttonSize === 'large' ? 'w-8 h-8' : 'w-6 h-6'} animate-pulse`} />
            <span className={`${classes.text['2xl']}`}>EMERGENCY HELP</span>
          </button>
        </div>

        {/* Core Pillars - 3 Button Grid */}
        <div className={`grid ${gridCols} ${classes.container.gap} mb-6`}>
          {/* Health Monitor */}
          <button
            onClick={handleHealthMonitor}
            className={`
              ${classes.container.padding}
              bg-white rounded-2xl
              ${classes.border} ${classes.shadow}
              ${classes.hover}
              transition-all duration-200
              hover:scale-105 active:scale-98
              text-left
            `}
          >
            <div className="flex items-center gap-4 mb-4">
              <div className={`${preferences.buttonSize === 'extra-large' ? 'p-5' : preferences.buttonSize === 'large' ? 'p-4' : 'p-3'} bg-red-100 rounded-xl`}>
                <Heart className={`${preferences.buttonSize === 'extra-large' ? 'w-12 h-12' : preferences.buttonSize === 'large' ? 'w-10 h-10' : 'w-8 h-8'} text-red-500`} />
              </div>
              <h3 className={`font-bold ${classes.text['2xl']} ${classes.textColor}`}>
                Health Monitor
              </h3>
            </div>

            <div className={`space-y-3 ${classes.container.padding} bg-gray-50 rounded-xl`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className={`${preferences.buttonSize === 'large' ? 'w-6 h-6' : 'w-5 h-5'} text-red-500`} />
                  <span className={`${classes.text.lg} ${classes.textColor}`}>Heart Rate</span>
                </div>
                <span className={`font-bold ${classes.text.xl} text-red-600`}>
                  {vitals.heartRate} bpm
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Moon className={`${preferences.buttonSize === 'large' ? 'w-6 h-6' : 'w-5 h-5'} text-blue-500`} />
                  <span className={`${classes.text.lg} ${classes.textColor}`}>Sleep Score</span>
                </div>
                <span className={`font-bold ${classes.text.xl} text-blue-600`}>
                  {vitals.sleepScore}%
                </span>
              </div>

              <p className={`${classes.text.base} text-gray-500 mt-2`}>
                Updated {vitals.lastUpdated}
              </p>
            </div>
          </button>

          {/* Social & Fun */}
          <button
            onClick={handleSocialFun}
            className={`
              ${classes.container.padding}
              bg-white rounded-2xl
              ${classes.border} ${classes.shadow}
              ${classes.hover}
              transition-all duration-200
              hover:scale-105 active:scale-98
              text-left
            `}
          >
            <div className="flex items-center gap-4 mb-4">
              <div className={`${preferences.buttonSize === 'extra-large' ? 'p-5' : preferences.buttonSize === 'large' ? 'p-4' : 'p-3'} bg-green-100 rounded-xl`}>
                <Users className={`${preferences.buttonSize === 'extra-large' ? 'w-12 h-12' : preferences.buttonSize === 'large' ? 'w-10 h-10' : 'w-8 h-8'} text-green-600`} />
              </div>
              <h3 className={`font-bold ${classes.text['2xl']} ${classes.textColor}`}>
                Social & Fun
              </h3>
            </div>

            <div className={`space-y-3`}>
              <div className={`flex items-center gap-3 ${classes.container.padding} bg-green-50 rounded-xl ${classes.hover}`}>
                <Phone className={`${preferences.buttonSize === 'large' ? 'w-6 h-6' : 'w-5 h-5'} text-green-600`} />
                <span className={`${classes.text.lg} ${classes.textColor}`}>Call Family</span>
              </div>

              <div className={`flex items-center gap-3 ${classes.container.padding} bg-green-50 rounded-xl ${classes.hover}`}>
                <Video className={`${preferences.buttonSize === 'large' ? 'w-6 h-6' : 'w-5 h-5'} text-green-600`} />
                <span className={`${classes.text.lg} ${classes.textColor}`}>Watch Videos</span>
              </div>

              <p className={`${classes.text.base} text-gray-500 mt-2`}>
                Classic movies & music
              </p>
            </div>
          </button>

          {/* Assistant Services */}
          <button
            onClick={handleAssistant}
            className={`
              ${classes.container.padding}
              bg-white rounded-2xl
              ${classes.border} ${classes.shadow}
              ${classes.hover}
              transition-all duration-200
              hover:scale-105 active:scale-98
              text-left
            `}
          >
            <div className="flex items-center gap-4 mb-4">
              <div className={`${preferences.buttonSize === 'extra-large' ? 'p-5' : preferences.buttonSize === 'large' ? 'p-4' : 'p-3'} bg-purple-100 rounded-xl`}>
                <Calendar className={`${preferences.buttonSize === 'extra-large' ? 'w-12 h-12' : preferences.buttonSize === 'large' ? 'w-10 h-10' : 'w-8 h-8'} text-purple-600`} />
              </div>
              <h3 className={`font-bold ${classes.text['2xl']} ${classes.textColor}`}>
                My Schedule
              </h3>
            </div>

            <div className={`space-y-3`}>
              {upcomingEvents.map(event => (
                <div
                  key={event.id}
                  className={`flex items-start gap-3 ${classes.container.padding} bg-purple-50 rounded-xl`}
                >
                  <Clock className={`${preferences.buttonSize === 'large' ? 'w-6 h-6' : 'w-5 h-5'} text-purple-600 flex-shrink-0 mt-1`} />
                  <div>
                    <p className={`font-semibold ${classes.text.lg} ${classes.textColor}`}>
                      {event.title}
                    </p>
                    <p className={`${classes.text.base} text-gray-600`}>
                      {event.time}
                    </p>
                  </div>
                </div>
              ))}

              <p className={`${classes.text.base} text-gray-500 mt-2 italic`}>
                📝 Updated by AI from your conversations
              </p>
            </div>
          </button>
        </div>

        {/* Footer Note */}
        <div className={`text-center ${classes.container.padding}`}>
          <p className={`${classes.text.base} text-gray-500`}>
            💙 Your companion is always here to help
          </p>
        </div>
      </div>
    </div>
  );
};
