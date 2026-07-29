/**
 * Error handling utilities for API responses
 */

/**
 * Extracts a readable error message from various error formats
 * Handles FastAPI validation errors, string errors, and objects
 *
 * @param err - Error object from API call
 * @param fallbackMessage - Default message if error cannot be parsed
 * @returns Human-readable error message string
 */
export function getErrorMessage(err: any, fallbackMessage: string = 'An error occurred'): string {
  console.error('Error:', err);

  // Handle network errors
  if (err.code === 'ECONNABORTED' || err.message === 'Network Error') {
    return 'Network error. Please check your internet connection.';
  }

  // Handle timeout errors
  if (err.code === 'ECONNREFUSED') {
    return 'Cannot connect to server. Please ensure the backend is running.';
  }

  // Handle response errors
  if (err.response?.data) {
    const errorData = err.response.data;

    // Handle FastAPI validation errors (array of error objects)
    if (Array.isArray(errorData.detail)) {
      const messages = errorData.detail.map((e: any) => {
        // Format: "field: message"
        if (e.loc && e.msg) {
          const field = e.loc[e.loc.length - 1]; // Get last item in location path
          return `${field}: ${e.msg}`;
        }
        return e.msg || JSON.stringify(e);
      });
      return messages.join(', ');
    }

    // Handle string error messages
    if (typeof errorData.detail === 'string') {
      return errorData.detail;
    }

    // Handle object error messages (convert to string)
    if (typeof errorData.detail === 'object' && errorData.detail !== null) {
      // Try to extract meaningful info from the object
      if (errorData.detail.message) {
        return errorData.detail.message;
      }
      return JSON.stringify(errorData.detail);
    }

    // Handle general error messages
    if (errorData.message && typeof errorData.message === 'string') {
      return errorData.message;
    }

    // Handle error field
    if (errorData.error && typeof errorData.error === 'string') {
      return errorData.error;
    }
  }

  // Handle axios errors with messages
  if (err.message && typeof err.message === 'string') {
    return err.message;
  }

  // Fallback to default message
  return fallbackMessage;
}

/**
 * Get HTTP status code from error
 */
export function getErrorStatus(err: any): number | null {
  return err.response?.status || null;
}

/**
 * Check if error is authentication related
 */
export function isAuthError(err: any): boolean {
  const status = getErrorStatus(err);
  return status === 401 || status === 403;
}

/**
 * Check if error is validation related
 */
export function isValidationError(err: any): boolean {
  const status = getErrorStatus(err);
  return status === 422;
}

/**
 * Check if error is a server error
 */
export function isServerError(err: any): boolean {
  const status = getErrorStatus(err);
  return status !== null && status >= 500;
}
