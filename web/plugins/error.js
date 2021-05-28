function showError($toast, error, err, fatal) {
  if (err.message === 'ERR_REDIRECT') return

  const response = err.response
  if (!response) {
    $toast.danger(err.name ? `${err.name} ${err.message}` : err.message)
  } else if (response.data && response.data.message) {
    $toast.danger(response.data.message)
  } else {
    $toast.danger(`${response.status} ${response.statusText}`)
  }

  if (process.server || fatal) {
    if (!err.response) {
      error({ statusCode: 599, message: err.message })
    } else {
      error({ statusCode: err.response.status, message: '' })
    }
  }
}

export default ({ $toast, error }, inject) => {
  inject('error', err => showError($toast, error, err, false))
  inject('fatal', err => showError($toast, error, err, true))
}
