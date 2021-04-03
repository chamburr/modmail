function JSONParse(source) {
  let index = 0
  let char = ' '

  const escapes = {
    '"': '"',
    '\\': '\\',
    '/': '/',
    b: '\b',
    f: '\f',
    n: '\n',
    r: '\r',
    t: '\t',
  }

  function next(c) {
    if (c && c !== char) {
      throw new Error(`Expected '${c}' instead of '${char}'`)
    }

    char = source.charAt(index)
    index += 1

    return char
  }

  function number() {
    let string = ''

    if (char === '-') {
      string = '-'
      next('-')
    }

    while (char >= '0' && char <= '9') {
      string += char
      next()
    }

    if (char === '.') {
      string += '.'

      while (next() && char >= '0' && char <= '9') {
        string += char
      }
    }

    const number = +string

    if (!isFinite(number)) {
      throw new SyntaxError('Bad number')
    } else if (string.length > 15) {
      return string
    } else {
      return number
    }
  }

  function string() {
    let string = ''

    if (char === '"') {
      let startAt = index

      while (next()) {
        if (char === '"') {
          if (index - 1 > startAt) string += source.substring(startAt, index - 1)
          next()

          return string
        }

        if (char === '\\') {
          if (index - 1 > startAt) string += source.substring(startAt, index - 1)
          next()

          if (char === 'u') {
            let code = 0

            for (let i = 0; i < 4; i++) {
              const hex = parseInt(next(), 16)
              if (!isFinite(hex)) {
                break
              } else {
                code = code * 16 + hex
              }
            }

            string += String.fromCharCode(code)
          } else if (typeof escapes[char] === 'string') {
            string += escapes[char]
          } else {
            break
          }

          startAt = index
        }
      }
    }

    throw new SyntaxError('Bad string')
  }

  function white() {
    while (char && char <= ' ') {
      next()
    }
  }

  function word() {
    if (char === 't') {
      next('t')
      next('r')
      next('u')
      next('e')
      return true
    } else if (char === 'f') {
      next('f')
      next('a')
      next('l')
      next('s')
      next('e')
      return false
    } else if (char === 'n') {
      next('n')
      next('u')
      next('l')
      next('l')
      return null
    }

    throw new SyntaxError(`Unexpected '${char}'`)
  }

  function array() {
    const array = []

    if (char === '[') {
      next('[')
      white()

      if (char === ']') {
        next(']')
        return array
      }

      while (char) {
        array.push(value())
        white()

        if (char === ']') {
          next(']')
          return array
        }

        next(',')
        white()
      }
    }

    throw new SyntaxError('Bad array')
  }

  function object() {
    const object = Object.create(null)

    if (char === '{') {
      next('{')
      white()

      if (char === '}') {
        next('}')
        return object
      }

      while (char) {
        const key = string()
        white()
        next(':')

        object[key] = value()

        white()

        if (char === '}') {
          next('}')
          return object
        }

        next(',')
        white()
      }
    }

    throw new SyntaxError('Bad object')
  }

  function value() {
    white()

    if (char === '{') {
      return object()
    } else if (char === '[') {
      return array()
    } else if (char === '"') {
      return string()
    } else if (char === '-') {
      return number()
    } else {
      return char >= '0' && char <= '9' ? number() : word()
    }
  }

  return value()
}

export default ({ $axios, res }) => {
  $axios.defaults.transformResponse = [
    function (data) {
      return JSON.parse(JSON.stringify(JSONParse(data)))
    },
  ]

  $axios.onResponse(response => {
    if (response.headers['set-cookie'] && process.server) {
      try {
        res.setHeader('Set-Cookie', [...response.headers['set-cookie']])
      } catch (err) {}
    }
    return response
  })
}
