const BASE = '/api/diary'

export const diaryApi = {
  create: (data) => post(`${BASE}`, data),
  list: (n = 10) => fetch(`${BASE}/recommend?n=${n}`).then(r => r.json()),
  search: (mode, q) => post(`${BASE}/search`, { mode, q }),
  get: (id) => fetch(`${BASE}/${id}`).then(r => r.json()),
  delete: (id) => fetch(`${BASE}/${id}`, { method: 'DELETE' }).then(r => r.json()),
  rate: (id, score) => post(`${BASE}/${id}/rate?score=${score}`, {}),
}

function post(url, body) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(r => r.json())
}
