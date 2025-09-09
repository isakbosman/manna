/**
 * Secure DOM utility functions to prevent XSS attacks
 */

/**
 * Safely set text content to prevent XSS
 */
export function setTextContent(element: HTMLElement, text: string): void {
  element.textContent = text;
}

/**
 * Create element with safe text content
 */
export function createElementWithText(
  tagName: string, 
  text: string, 
  className?: string
): HTMLElement {
  const element = document.createElement(tagName);
  element.textContent = text;
  if (className) {
    element.className = className;
  }
  return element;
}

/**
 * Sanitize HTML string (basic implementation - consider using DOMPurify for production)
 */
export function sanitizeHTML(html: string): string {
  const div = document.createElement('div');
  div.textContent = html;
  return div.innerHTML;
}
