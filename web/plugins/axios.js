export default ({ $axios, res }) => {
  $axios.onResponse(response => {
    if (response.headers['set-cookie'] && process.server) {
      try {
        res.setHeader('Set-Cookie', [...response.headers['set-cookie']])
      } catch (err) {}
    }
    return response
  })
}
