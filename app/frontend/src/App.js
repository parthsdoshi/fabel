import React from 'react';
import io from 'socket.io-client'

import 'bulma/css/bulma.css'

class App extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      files: []
    }
  }

  componentDidMount() {
    let socket = io()
    socket.on('connect', () => {
      console.log('connected')

      this.socket = socket

      socket.emit('getAllFiles', (files) => {
        this.setState({
          files: files
        })
        socket.on('newFile', (file) => {
          this.setState({
            files: [file].concat(this.state.files)
          })
        })
      })

      // socket.emit('retrieveAllFiles', '', (files) => {
        // console.log(files)
        // this.setState = ({
          // 'files': files
        // })
      // })
    })
  }

  openFile = (filepath) => {
    if (window.socket) {
      window.socket.emit('openFile', filepath, (error) => {
        console.log(error)
      })
    }
  }

  render() {
    return (
      <div className='container is-fluid'>
        <table className="table is-hoverable is-fullwidth">
          <thead>
            <tr>
              <th>File Name</th>
              <th>File Path</th>
              <th>Tags</th>
              {/* <th title="filename">Suggested Tags</th> */}
            </tr>
          </thead>
          <tfoot>
            {this.state.files.map((file) => {
              return (
                <tr onClick={() => {this.openFile(file.path)}}>
                  <td>{file.name}</td>
                  <td>{file.path}</td>
                  <td>
                    <div className='tags are-small'>
                      {file.tags.map((tag) => {
                        return (
                            <span className='tag is-success'>{tag}</span>
                        )
                      })}
                    </div>
                  </td>
                  {/* <td>{file.suggested_tags}</td> */}
                </tr>
              )
            })}
          </tfoot>
        </table>
      </div>
    )
  }
}

export default App;
