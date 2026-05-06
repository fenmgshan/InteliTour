const BASE = '/api/diary'

export const diaryApi = {
  create: (data) => post(`${BASE}/create`, data),
  list: (n = 10) => post(`${BASE}/recommend`, { n }),
  search: (q, n = 10) => post(`${BASE}/search`, { q, n }),
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
