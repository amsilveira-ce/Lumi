// useUserPreferences.ts - Simulates fetching user preferences from Context Engine
import { useState, useEffect } from 'react';

export interface UserPreferences {
  textSize: 'normal' | 'large' | 'extra-large';
  contrast: 'normal' | 'high';
  buttonSize: 'standard' | 'large' | 'extra-large';
}

export interface UserProfile {
  userName: string;
  age: number;
  cognitiveComfort: string;
}

export interface ContextResponse {
  userProfile: UserProfile;
  preferences: UserPreferences;
  dailyInsight: string;
  vitals: {
    heartRate: number;
    sleepScore: number;
    lastUpdated: string;
  };
  upcomingEvents: Array<{
    id: string;
    title: string;
    time: string;
    type: 'appointment' | 'medication' | 'social';
  }>;
  emergencyContacts: Array<{
    id: string;
    name: string;
    relation: string;
    phone: string;
  }>;
}

const formatRelativeDayLabel = (targetDate: Date, now: Date) => {
  const startOfNow = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfTarget = new Date(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate());
  const msInDay = 24 * 60 * 60 * 1000;
  const dayDiff = Math.round((startOfTarget.getTime() - startOfNow.getTime()) / msInDay);

  if (dayDiff <= 0) return 'Today';
  if (dayDiff === 1) return 'Tomorrow';
  return targetDate.toLocaleDateString('en-US', { weekday: 'long' });
};

const formatTimeLabel = (hours: number, minutes: number, now: Date) => {
  const targetDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hours, minutes);
  const dayLabel = formatRelativeDayLabel(targetDate, now);
  const timeLabel = targetDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  return `${dayLabel} at ${timeLabel}`;
};

const formatRelativeUpdated = (minutesAgo: number) => {
  if (minutesAgo < 60) {
    return `${minutesAgo} minutes ago`;
  }
  const hours = Math.round(minutesAgo / 60);
  return `${hours} hours ago`;
};

const getTimeOfDay = (now: Date) => {
  const hour = now.getHours();
  if (hour < 12) return 'morning';
  if (hour < 18) return 'afternoon';
  return 'evening';
};

// Mock data simulating backend Context Engine response
const buildMockContextResponse = (now: Date = new Date()): ContextResponse => {
  const timeOfDay = getTimeOfDay(now);
  const weekday = now.toLocaleDateString('en-US', { weekday: 'long' });

  const tomorrow = new Date(now);
  tomorrow.setDate(now.getDate() + 1);

  return {
    userProfile: {
      userName: 'Grandpa Joe',
      age: 78,
      cognitiveComfort: 'intermediate'
    },
    preferences: {
      textSize: 'large',
      contrast: 'high',
      buttonSize: 'large'
    },
    dailyInsight: `It's ${weekday} ${timeOfDay}, Grandpa Joe. Remember to drink water after your walk!`,
    vitals: {
      heartRate: 72,
      sleepScore: 85,
      lastUpdated: formatRelativeUpdated(120)
    },
    upcomingEvents: [
      {
        id: '1',
        title: 'Dr. Smith appointment',
        time: formatTimeLabel(14, 0, now),
        type: 'appointment'
      },
      {
        id: '2',
        title: 'Take evening medication',
        time: formatTimeLabel(18, 0, now),
        type: 'medication'
      },
      {
        id: '3',
        title: 'Call with Sarah',
        time: formatTimeLabel(10, 0, tomorrow),
        type: 'social'
      }
    ],
    emergencyContacts: [
      {
        id: '1',
        name: 'Dr. Sarah Johnson',
        relation: 'Primary Doctor',
        phone: '+1-555-0101'
      },
      {
        id: '2',
        name: 'John Smith',
        relation: 'Son',
        phone: '+1-555-0102'
      },
      {
        id: '3',
        name: 'Mary Williams',
        relation: 'Daughter',
        phone: '+1-555-0103'
      }
    ]
  };
};

/**
 * Custom hook that simulates fetching user preferences and context from backend
 * In production, this would make an API call to the Context Retrieval Engine
 */
export const useUserPreferences = (): {
  contextData: ContextResponse | null;
  isLoading: boolean;
  error: string | null;
} => {
  const [contextData, setContextData] = useState<ContextResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate API call delay
    const fetchContextData = async () => {
      try {
        setIsLoading(true);

        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 500));

        // In production, this would be:
        // const response = await fetch('http://localhost:8082/api/context');
        // const data = await response.json();

        setContextData(buildMockContextResponse());
        setError(null);
      } catch (err) {
        setError('Failed to load user context');
        console.error('Context fetch error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchContextData();
  }, []);

  return { contextData, isLoading, error };
};

/**
 * Helper function to get Tailwind classes based on preferences
 */
export const getPreferenceClasses = (preferences: UserPreferences | undefined) => {
  if (!preferences) {
    return {
      text: {
        base: 'text-base',
        lg: 'text-lg',
        xl: 'text-xl',
        '2xl': 'text-2xl',
        '3xl': 'text-3xl'
      },
      button: {
        height: 'h-12',
        padding: 'px-6 py-3',
        text: 'text-base'
      },
      container: {
        gap: 'gap-4',
        padding: 'p-4'
      },
      border: 'border border-gray-200',
      shadow: 'shadow-md',
      bg: 'bg-white',
      textColor: 'text-gray-700',
      hover: 'hover:bg-gray-50'
    };
  }

  // Text size classes
  type TextScale = {
    base: string;
    lg: string;
    xl: string;
    '2xl': string;
    '3xl': string;
  };
  const textClasses: Record<UserPreferences['textSize'], TextScale> = {
    normal: {
      base: 'text-base',
      lg: 'text-lg',
      xl: 'text-xl',
      '2xl': 'text-2xl',
      '3xl': 'text-3xl'
    },
    large: {
      base: 'text-lg',
      lg: 'text-xl',
      xl: 'text-2xl',
      '2xl': 'text-3xl',
      '3xl': 'text-4xl'
    },
    'extra-large': {
      base: 'text-xl',
      lg: 'text-2xl',
      xl: 'text-3xl',
      '2xl': 'text-4xl',
      '3xl': 'text-5xl'
    }
  };

  // Button size classes
  type ButtonScale = {
    height: string;
    padding: string;
    text: string;
  };
  const buttonClasses: Record<UserPreferences['buttonSize'], ButtonScale> = {
    standard: {
      height: 'h-12',
      padding: 'px-6 py-3',
      text: 'text-base'
    },
    large: {
      height: 'h-16',
      padding: 'px-8 py-4',
      text: 'text-lg'
    },
    'extra-large': {
      height: 'h-20',
      padding: 'px-10 py-6',
      text: 'text-xl'
    }
  };

  // Container spacing
  type ContainerScale = {
    gap: string;
    padding: string;
  };
  const containerClasses: Record<'normal' | 'large' | 'extra-large', ContainerScale> = {
    normal: {
      gap: 'gap-4',
      padding: 'p-4'
    },
    large: {
      gap: 'gap-6',
      padding: 'p-6'
    },
    'extra-large': {
      gap: 'gap-8',
      padding: 'p-8'
    }
  };

  // Contrast-based styling
  type ContrastStyle = {
    border: string;
    shadow: string;
    bg: string;
    textColor: string;
    hover: string;
  };
  const contrastClasses: Record<UserPreferences['contrast'], ContrastStyle> = {
    normal: {
      border: 'border border-gray-200',
      shadow: 'shadow-md',
      bg: 'bg-white',
      textColor: 'text-gray-700',
      hover: 'hover:bg-gray-50'
    },
    high: {
      border: 'border-2 border-black',
      shadow: '',
      bg: 'bg-white',
      textColor: 'text-black',
      hover: 'hover:bg-gray-100'
    }
  };

  return {
    text: textClasses[preferences.textSize],
    button: buttonClasses[preferences.buttonSize],
    container: containerClasses[preferences.buttonSize === 'extra-large' ? 'extra-large' : preferences.buttonSize === 'large' ? 'large' : 'normal'],
    ...contrastClasses[preferences.contrast]
  };
};
