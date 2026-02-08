import React, { useState } from 'react';
import { StepProps } from './types';
import './DailyRoutinesStep.css';

interface DailyRoutine {
  id: string;
  type: 'medication' | 'appointment';
  time: string;
  description: string;
}

export const DailyRoutinesStep: React.FC<StepProps> = ({
  data,
  onSubmit,
  isLoading,
  errors
}) => {
  const [routines, setRoutines] = useState<DailyRoutine[]>([]);

  const title = data.title || 'Your Daily Routines';
  const subtitle = data.subtitle || 'Help us remind you about important tasks';
  const instructions = data.instructions || 'Add any medication times or appointments you want to remember';

  const addRoutine = (type: 'medication' | 'appointment') => {
    const newRoutine: DailyRoutine = {
      id: `routine_${Date.now()}`,
      type,
      time: '09:00',
      description: ''
    };
    setRoutines(prev => [...prev, newRoutine]);
  };

  const updateRoutine = (id: string, field: keyof DailyRoutine, value: string) => {
    setRoutines(prev =>
      prev.map(routine =>
        routine.id === id ? { ...routine, [field]: value } : routine
      )
    );
  };

  const removeRoutine = (id: string) => {
    setRoutines(prev => prev.filter(routine => routine.id !== id));
  };

  const handleSubmit = () => {
    // Filter out routines without descriptions
    const validRoutines = routines.filter(r => r.description.trim() !== '');
    onSubmit({ daily_routines: validRoutines });
  };

  return (
    <div className="daily-routines-step">
      <div className="step-header">
        <h1 className="step-title">{title}</h1>
        {subtitle && <p className="step-subtitle">{subtitle}</p>}
        {instructions && <p className="step-instructions">📋 {instructions}</p>}
      </div>

      <div className="add-routine-buttons">
        <button
          className="add-routine-btn medication"
          onClick={() => addRoutine('medication')}
          disabled={isLoading}
        >
          <span className="btn-icon">💊</span>
          <span>Add Medication</span>
        </button>
        <button
          className="add-routine-btn appointment"
          onClick={() => addRoutine('appointment')}
          disabled={isLoading}
        >
          <span className="btn-icon">📅</span>
          <span>Add Appointment</span>
        </button>
      </div>

      <div className="routines-list">
        {routines.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">⏰</div>
            <p>No routines added yet</p>
            <p className="empty-hint">Click the buttons above to add medication times or appointments</p>
          </div>
        ) : (
          routines.map((routine) => (
            <div key={routine.id} className={`routine-card ${routine.type}`}>
              <div className="routine-type-indicator">
                {routine.type === 'medication' ? '💊' : '📅'}
              </div>

              <div className="routine-fields">
                <div className="field-group">
                  <label htmlFor={`time-${routine.id}`}>Time</label>
                  <input
                    id={`time-${routine.id}`}
                    type="time"
                    className="routine-input time-input"
                    value={routine.time}
                    onChange={(e) => updateRoutine(routine.id, 'time', e.target.value)}
                    disabled={isLoading}
                  />
                </div>

                <div className="field-group description-group">
                  <label htmlFor={`description-${routine.id}`}>
                    {routine.type === 'medication' ? 'Medication Name' : 'Appointment Details'}
                  </label>
                  <input
                    id={`description-${routine.id}`}
                    type="text"
                    className="routine-input description-input"
                    placeholder={routine.type === 'medication' ? 'e.g., Blood pressure medication' : 'e.g., Doctor appointment'}
                    value={routine.description}
                    onChange={(e) => updateRoutine(routine.id, 'description', e.target.value)}
                    disabled={isLoading}
                  />
                </div>
              </div>

              <button
                className="remove-btn"
                onClick={() => removeRoutine(routine.id)}
                disabled={isLoading}
                aria-label="Remove routine"
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>

      {errors?.general && (
        <div className="error-message" role="alert">
          {errors.general}
        </div>
      )}

      <div className="step-actions">
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={isLoading}
        >
          {isLoading ? 'Processing...' : routines.length === 0 ? 'Skip for Now' : 'Continue'}
        </button>
      </div>
    </div>
  );
};
