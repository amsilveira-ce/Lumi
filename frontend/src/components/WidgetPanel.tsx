import React from 'react';
import { MoodSelector } from './widgets/MoodSelector';
import { ActivitySuggestions } from './widgets/ActivitySuggestions';
import { ReminderList } from './widgets/ReminderList';
import { ContactSelector } from './widgets/ContactSelector';
import './WidgetPanel.css';

interface Widget {
  id: string;
  type: string;
  props: any;
  visible: boolean;
}

interface WidgetPanelProps {
  widgets: Widget[];
}

const WIDGET_MAP: Record<string, React.ComponentType<any>> = {
  MoodSelector,
  ActivitySuggestions,
  ReminderList,
  ContactSelector
};

export const WidgetPanel: React.FC<WidgetPanelProps> = ({ widgets }) => {
  return (
    <div className="widget-panel">
      <div className="widget-panel-header">
        <h2>🎛️ Quick Actions</h2>
      </div>

      <div className="widget-list">
        {widgets.length === 0 ? (
          <div className="empty-widgets">
            <div className="empty-icon">💡</div>
            <p>No widgets active yet</p>
            <p className="empty-hint">
              Widgets will appear here based on our conversation
            </p>
          </div>
        ) : (
          widgets.map((widget) => {
            const Component = WIDGET_MAP[widget.type];
            if (!Component) {
              return (
                <div key={widget.id} className="widget unknown-widget">
                  <p>Unknown widget type: {widget.type}</p>
                </div>
              );
            }

            return (
              <div key={widget.id} className="widget-wrapper">
                <Component {...widget.props} />
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
