import React, { useState } from 'react';
import { StepProps } from './types';
import './EmergencyContactsStep.css';

interface EmergencyContact {
  id: string;
  name: string;
  phone: string;
  relation: string;
}

// Mock contacts for MVP
const MOCK_CONTACTS: EmergencyContact[] = [
  { id: '1', name: 'Dr. Sarah Johnson', phone: '+1-555-0101', relation: 'Primary Doctor' },
  { id: '2', name: 'John Smith', phone: '+1-555-0102', relation: 'Son' },
  { id: '3', name: 'Mary Williams', phone: '+1-555-0103', relation: 'Daughter' },
  { id: '4', name: 'Robert Brown', phone: '+1-555-0104', relation: 'Neighbor' },
  { id: '5', name: 'Lisa Davis', phone: '+1-555-0105', relation: 'Sister' }
];

export const EmergencyContactsStep: React.FC<StepProps> = ({
  data,
  onSubmit,
  isLoading,
  errors
}) => {
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);

  const title = data.title || 'Emergency Contacts';
  const subtitle = data.subtitle || 'Who should we notify in case of emergency?';
  const instructions = data.instructions || 'Please select 1-3 people we can contact if needed';

  const handleContactToggle = (contactId: string) => {
    setSelectedContacts(prev => {
      if (prev.includes(contactId)) {
        // Deselect
        return prev.filter(id => id !== contactId);
      } else if (prev.length < 3) {
        // Select (max 3)
        return [...prev, contactId];
      } else {
        // Already at max, replace last one
        return [...prev.slice(0, 2), contactId];
      }
    });
  };

  const handleSubmit = () => {
    if (selectedContacts.length === 0) {
      return;
    }

    const selectedContactData = MOCK_CONTACTS.filter(c =>
      selectedContacts.includes(c.id)
    );

    onSubmit({ emergency_contacts: selectedContactData });
  };

  return (
    <div className="emergency-contacts-step">
      <div className="step-header">
        <h1 className="step-title">{title}</h1>
        {subtitle && <p className="step-subtitle">{subtitle}</p>}
        {instructions && <p className="step-instructions">📋 {instructions}</p>}
      </div>

      <div className="contacts-selection-info">
        <span className="selection-count">
          {selectedContacts.length} of 3 selected
        </span>
      </div>

      <div className="contacts-list">
        {MOCK_CONTACTS.map((contact) => {
          const isSelected = selectedContacts.includes(contact.id);
          return (
            <button
              key={contact.id}
              className={`contact-card ${isSelected ? 'selected' : ''}`}
              onClick={() => handleContactToggle(contact.id)}
              disabled={isLoading}
            >
              <div className="contact-icon">
                {isSelected ? '✅' : '👤'}
              </div>
              <div className="contact-info">
                <div className="contact-name">{contact.name}</div>
                <div className="contact-relation">{contact.relation}</div>
                <div className="contact-phone">{contact.phone}</div>
              </div>
            </button>
          );
        })}
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
          disabled={selectedContacts.length === 0 || isLoading}
        >
          {isLoading ? 'Processing...' : 'Continue'}
        </button>
      </div>
    </div>
  );
};
