const BASE = '/api/diary'

export const diaryApi = {
  create: (data) => post(`${BASE}`, data),
  list: (n = 10) => fetch(`${BASE}/recommend?n=${n}`).then(r => r.json()),
  search: (mode, q) => post(`${BASE}/search`, { mode, q }),
  get: (id) => fetch(`${BASE}/${id}`).then(r => r.json()),
  delete: (id) => fetch(`${BASE}/${id}`, { method: 'DELETE' }).then(r => r.json()),
}

function post(url, body) {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(r => r.json())
}
