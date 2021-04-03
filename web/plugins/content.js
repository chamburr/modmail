function getValue(element) {
  return element.value ? element.value : element.children[0].value
}

export default ({ $content }, inject) => {
  inject('getContent', async (name, json = true) => {
    const content = await $content(name).fetch()

    if (json) {
      const data = []
      for (const element of content.body.children) {
        if (element.tag === 'h1' || element.tag === 'h2') {
          data.push({
            name: getValue(element.children[0]),
            description: '',
          })
        } else if (element.tag === 'p') {
          data[data.length - 1].description += getValue(element.children[0]).replace(/\n/g, ' ')
        } else if (element.tag === 'ul') {
          for (const element2 of element.children) {
            if (element2.tag === 'li') {
              const value = element2.children.map(element3 => getValue(element3)).join('')
              const key = value.split(': ')[0].toLowerCase()
              data[data.length - 1][key] = value.split(': ').slice(1).join(': ')
            }
          }
        } else if (element.type === 'text' && element.value === '\n') {
          data[data.length - 1].description += '\n\n'
        }
      }

      for (const [index] of data.entries()) {
        data[index].description = data[index].description.trim()
      }

      return data
    }

    if (!json) {
      content.body.children.forEach((element, index) => {
        if (element.tag === 'h1') {
          element.tag = 'h2'
          if (index !== 0) {
            element.props.class = 'mt-4'
          }
        } else if (element.tag === 'p' || element.tag === 'ul') {
          element.children.forEach(element2 => {
            if (element2.tag === 'em') {
              element2.tag = 'span'
              element2.props.class = 'text-light'
            } else if (element2.tag === 'a') {
              element2.tag = 'span'
              element2.props = {}
            } else if (element2.tag === 'li') {
              element2.children.forEach(element3 => {
                if (element3.tag === 'a') {
                  element3.tag = 'span'
                  element3.props = {}
                }
              })
            }
          })
        }
      })
      return content
    }
  })
}
