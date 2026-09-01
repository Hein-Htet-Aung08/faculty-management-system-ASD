const apiEndpoints = [
  '/api/performance-reviews',
  '/api/development-goals',
  '/api/training-programs',
  '/api/staff-training',
  '/api/development-recommendations'
];

async function loadRecords() {
  const list = document.getElementById('records-list');

  try {
    const items = await Promise.all(apiEndpoints.map(async (endpoint) => {
      const response = await fetch(endpoint);
      const data = await response.json();
      return `<li><strong>${endpoint}</strong>: ${data.message}</li>`;
    }));

    list.innerHTML = items.join('');
  } catch (error) {
    list.innerHTML = `<li>Unable to load records: ${error.message}</li>`;
  }
}

window.addEventListener('DOMContentLoaded', loadRecords);
