/**
 * Format timestamp for message display.
 * @param {Date|string|number} [date] - Optional date object or timestamp
 * @returns {string} Formatted time string e.g. "10:00 AM"
 */
export const formatMessageTime = (date = new Date()) => {
  const d = date instanceof Date ? date : new Date(date);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
};
