import React, { useState } from 'react';
import './ReminderList.css';

interface Reminder {
  id: string;
  title: string;
  time: string;
  completed: boolean;
  type: 'medication' | 'appointment' | 'task';
}

interface ReminderListProps {
  reminders?: Reminder[];
}

const DEFAULT_REMINDERS: Reminder[] = [
  {
    id: '1',
    title: 'Take morning medication',
    time: '9:00 AM',
    completed: false,
    type: 'medication'
  },
  {
    id: '2',
    title: 'Doctor appointment',
    time: '2:00 PM',
    completed: false,
    type: 'appointment'
  },
  {
    id: '3',
    title: 'Evening walk',
    time: '5:00 PM',
    completed: false,
    type: 'task'
  }
];

const TYPE_ICONS = {
  medication: '💊',
  appointment: '📅',
  task: '✓'
};

export const ReminderList: React.FC<ReminderListProps> = ({ reminders }) => {
  const [localReminders, setLocalReminders] = useState<Reminder[]>(
    reminders || DEFAULT_REMINDERS
  );

  const toggleReminder = (id: string) => {
    setLocalReminders(prev =>
      prev.map(reminder =>
        reminder.id === id
          ? { ...reminder, completed: !reminder.completed }
          : reminder
      )
    );
    console.log('Reminder toggled:', id);
    // In a real app, this would sync with the backend
  };

  const incompleteCount = localReminders.filter(r => !r.completed).length;

  return (
    <div className="reminder-list widget">
      <div className="reminder-header">
        <h3 className="widget-title">⏰ Your Reminders</h3>
        {incompleteCount > 0 && (
          <span className="reminder-badge">{incompleteCount}</span>
        )}
      </div>
      <p className="widget-subtitle">Today's schedule</p>

      <div className="reminders">
        {localReminders.map((reminder) => (
          <div
            key={reminder.id}
            className={`reminder-item ${reminder.completed ? 'completed' : ''}`}
          >
            <button
              className="reminder-checkbox"
              onClick={() => toggleReminder(reminder.id)}
              aria-label={reminder.completed ? 'Mark incomplete' : 'Mark complete'}
            >
              {reminder.completed ? '✓' : ''}
            </button>

            <div className="reminder-icon">
              {TYPE_ICONS[reminder.type]}
            </div>

            <div className="reminder-content">
              <div className="reminder-title">{reminder.title}</div>
              <div className="reminder-time">{reminder.time}</div>
            </div>
          </div>
        ))}
      </div>

      {localReminders.every(r => r.completed) && (
        <div className="all-done-message">
          <span className="celebration-icon">🎉</span>
          <p>All done for today! Great job!</p>
        </div>
      )}
    </div>
  );
};
