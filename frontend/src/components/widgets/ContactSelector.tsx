import React, { useState } from 'react';
import { Phone, User, Heart, Stethoscope, Users } from 'lucide-react';

interface Contact {
  id: string;
  name: string;
  relation: string;
  phone: string;
  preferred_method: 'call' | 'message';
  icon?: React.ReactNode;
}

interface ContactSelectorProps {
  widget_id: string;
  requested_contact?: string;
  message?: string;
  onContactSelect?: (contact: Contact) => void;
}

export const ContactSelector: React.FC<ContactSelectorProps> = ({
  widget_id: _widget_id,
  requested_contact = 'someone',
  message: _message,
  onContactSelect
}) => {
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  const [calling, setCalling] = useState(false);

  // Mock emergency contacts (in production, fetch from backend/Google Contacts API)
  const emergencyContacts: Contact[] = [
    {
      id: '1',
      name: 'Tommy',
      relation: 'Grandson',
      phone: '555-0199',
      preferred_method: 'call',
      icon: <Heart className="w-6 h-6 text-red-500" />
    },
    {
      id: '2',
      name: 'Sarah',
      relation: 'Daughter',
      phone: '555-0156',
      preferred_method: 'call',
      icon: <Heart className="w-6 h-6 text-pink-500" />
    },
    {
      id: '3',
      name: 'Dr. Smith',
      relation: 'Doctor',
      phone: '555-0900',
      preferred_method: 'message',
      icon: <Stethoscope className="w-6 h-6 text-blue-500" />
    },
    {
      id: '4',
      name: 'John',
      relation: 'Son',
      phone: '555-0142',
      preferred_method: 'call',
      icon: <Heart className="w-6 h-6 text-blue-600" />
    }
  ];

  // Try to find the requested contact
  const suggestedContact = emergencyContacts.find(contact =>
    contact.relation.toLowerCase().includes(requested_contact.toLowerCase()) ||
    contact.name.toLowerCase().includes(requested_contact.toLowerCase())
  );

  const handleContactClick = (contact: Contact) => {
    setSelectedContact(contact);
  };

  const handleCall = (contact: Contact) => {
    setCalling(true);
    console.log(`📞 Initiating call to ${contact.name} (${contact.phone})`);

    // In production, integrate with telephony API (Twilio, native tel: protocol, etc.)
    // For now, simulate call initiation
    setTimeout(() => {
      // Simulate call being placed
      if (typeof window !== 'undefined' && window.location.protocol === 'http:') {
        // Try native tel: link
        window.location.href = `tel:${contact.phone}`;
      } else {
        alert(`Mock: Calling ${contact.name} at ${contact.phone}\n\nIn production, this would initiate a real call via Twilio or device telephony.`);
      }

      setCalling(false);

      // Callback if provided
      if (onContactSelect) {
        onContactSelect(contact);
      }
    }, 1000);
  };

  return (
    <div className="contact-selector-widget bg-white rounded-lg shadow-lg p-6 my-4 border-2 border-blue-300">
      <div className="flex items-center gap-3 mb-4">
        <Phone className="w-8 h-8 text-blue-600" />
        <div>
          <h3 className="text-2xl font-bold text-gray-800">Who would you like to contact?</h3>
          {requested_contact && requested_contact !== 'someone' && (
            <p className="text-lg text-gray-600 mt-1">
              Looking for your <span className="font-semibold text-blue-600">{requested_contact}</span>
            </p>
          )}
        </div>
      </div>

      {/* Suggested Contact (if found) */}
      {suggestedContact && (
        <div className="mb-6 p-4 bg-blue-50 rounded-lg border-2 border-blue-400">
          <p className="text-sm text-blue-800 font-semibold mb-3">✨ Suggested Contact</p>
          <div
            className="flex items-center justify-between p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer border-2 border-blue-500"
            onClick={() => handleContactClick(suggestedContact)}
          >
            <div className="flex items-center gap-4">
              <div className="flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full">
                {suggestedContact.icon || <User className="w-8 h-8 text-blue-600" />}
              </div>
              <div>
                <h4 className="text-2xl font-bold text-gray-900">{suggestedContact.name}</h4>
                <p className="text-lg text-gray-600">{suggestedContact.relation}</p>
                <p className="text-md text-gray-500 font-mono">{suggestedContact.phone}</p>
              </div>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleCall(suggestedContact);
              }}
              disabled={calling}
              className="flex items-center gap-2 px-6 py-4 bg-green-600 text-white text-xl font-semibold rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors shadow-md"
              style={{ minWidth: '140px', minHeight: '64px' }}
            >
              <Phone className="w-6 h-6" />
              {calling ? 'Calling...' : 'Call Now'}
            </button>
          </div>
        </div>
      )}

      {/* All Emergency Contacts */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-6 h-6 text-gray-600" />
          <h4 className="text-xl font-semibold text-gray-700">All Emergency Contacts</h4>
        </div>
        <div className="space-y-3">
          {emergencyContacts.map((contact) => (
            <div
              key={contact.id}
              className={`flex items-center justify-between p-4 rounded-lg border-2 transition-all cursor-pointer ${
                selectedContact?.id === contact.id
                  ? 'bg-blue-50 border-blue-500 shadow-md'
                  : 'bg-gray-50 border-gray-300 hover:border-gray-400 hover:shadow-sm'
              }`}
              onClick={() => handleContactClick(contact)}
            >
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-14 h-14 bg-white rounded-full shadow-sm">
                  {contact.icon || <User className="w-6 h-6 text-gray-600" />}
                </div>
                <div>
                  <h5 className="text-xl font-bold text-gray-900">{contact.name}</h5>
                  <p className="text-md text-gray-600">{contact.relation}</p>
                  <p className="text-sm text-gray-500 font-mono">{contact.phone}</p>
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleCall(contact);
                }}
                disabled={calling}
                className={`flex items-center gap-2 px-5 py-3 text-lg font-semibold rounded-lg transition-colors shadow-sm ${
                  contact.preferred_method === 'call'
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                } disabled:bg-gray-400 disabled:cursor-not-allowed`}
                style={{ minWidth: '120px', minHeight: '56px' }}
              >
                <Phone className="w-5 h-5" />
                {calling
                  ? 'Calling...'
                  : contact.preferred_method === 'call'
                  ? 'Call'
                  : 'Message'}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Helper Text */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-md text-gray-600 text-center">
          💡 <span className="font-semibold">Tip:</span> Click on any contact to call them. In an emergency, dial 911 directly.
        </p>
      </div>

      {/* Call Status (if calling) */}
      {calling && (
        <div className="mt-4 p-4 bg-yellow-50 border-2 border-yellow-400 rounded-lg flex items-center gap-3">
          <div className="animate-pulse">
            <Phone className="w-6 h-6 text-yellow-600" />
          </div>
          <p className="text-lg font-semibold text-yellow-800">
            Connecting your call...
          </p>
        </div>
      )}
    </div>
  );
};

export default ContactSelector;
