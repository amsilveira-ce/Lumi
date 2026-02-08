import React from 'react';
import './ActivitySuggestions.css';

interface Activity {
  id: string;
  title: string;
  description: string;
  icon: string;
  duration: string;
}

interface ActivitySuggestionsProps {
  activities?: Activity[];
}

const DEFAULT_ACTIVITIES: Activity[] = [
  {
    id: '1',
    title: 'Take a Walk',
    description: 'A short walk in the garden or around the block',
    icon: '🚶',
    duration: '15 min'
  },
  {
    id: '2',
    title: 'Call a Friend',
    description: 'Catch up with someone you care about',
    icon: '📞',
    duration: '20 min'
  },
  {
    id: '3',
    title: 'Listen to Music',
    description: 'Relax with your favorite songs',
    icon: '🎵',
    duration: '30 min'
  },
  {
    id: '4',
    title: 'Read a Book',
    description: 'Enjoy a chapter of your current book',
    icon: '📚',
    duration: '25 min'
  }
];

export const ActivitySuggestions: React.FC<ActivitySuggestionsProps> = ({ activities }) => {
  const displayActivities = activities || DEFAULT_ACTIVITIES;

  const handleActivityClick = (activity: Activity) => {
    console.log('Activity selected:', activity.title);
    // In a real app, this would interact with the agent
  };

  return (
    <div className="activity-suggestions widget">
      <h3 className="widget-title">🎯 Activity Ideas</h3>
      <p className="widget-subtitle">Here are some things you might enjoy</p>

      <div className="activity-list">
        {displayActivities.map((activity) => (
          <button
            key={activity.id}
            className="activity-card"
            onClick={() => handleActivityClick(activity)}
          >
            <div className="activity-icon">{activity.icon}</div>
            <div className="activity-content">
              <div className="activity-header">
                <h4 className="activity-title">{activity.title}</h4>
                <span className="activity-duration">{activity.duration}</span>
              </div>
              <p className="activity-description">{activity.description}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
