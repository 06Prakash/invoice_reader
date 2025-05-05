// Mock login function
export const login = async (username, password) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        access_token: 'mock-jwt-token',
        refresh_token: 'mock-refresh-token',
        special_admin: true
      });
    }, 1000);
  });
};

// Mock token refresh
export const refreshToken = async () => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        access_token: 'new-mock-jwt-token'
      });
    }, 1000);
  });
};