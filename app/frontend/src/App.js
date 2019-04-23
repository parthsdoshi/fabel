import React from 'react';
import io from 'socket.io-client'
import Modal from './Modal'

import 'bulma/css/bulma.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

class App extends React.Component {
    constructor(props) {
        super(props)
        this.state = {
            files: {0: { 'id': 0, 'tags': ['test', 'test2'], 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' }},
            modal: {
                active: false,
                fileId: -1,
                textField: ''
            }
        }
    }

    componentDidMount() {
        let socket = io()
        socket.on('connect', () => {
            console.log('connected')

            window.socket = socket

            socket.emit('getAllFiles', (files) => {
                console.log(files)
                if (files['error'] === 0) {
                    this.setState({
                        files: files['payload']
                    })
                }
                socket.on('newFile', (file) => {
                    let files = {...this.state.files}
                    files[file.id] = file
                    this.setState({
                        files: files
                    })
                })
                // socket.on('updateFile', (file) => {
                //     for
                // })
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
            window.socket.emit('openFile', filepath, (ack) => {
                console.log(ack)
            })
        }
    }

    activateModal = (fileId) => {
        this.setState({
            modal: {...this.state.modal, active: true, fileId: fileId}
        })
    }

    addTag = (fileId, tag) => {
        console.log(fileId)
        console.log(tag)
        this.closeModal()
        if (window.socket) {
            let file = {...this.state.files[fileId], tags: [...this.state.files[fileId].tags, tag]}
            let files = {...this.state.files}
            files[file.id] = file
            this.setState({
                files: files
            })
            window.socket.emit('addTag', fileId, tag, (ack) => {
                console.log(ack)
                if (ack.payload) {
                    files = {...this.state.files}
                    files[fileId] = ack.payload
                    this.setState({
                        files: files
                    })
                }
            })
        }
    }

    removeTag = (fileId, tag) => {
        console.log(fileId)
        console.log(tag)
        if (window.socket) {
            let file = {...this.state.files[fileId], tags: this.state.files[fileId].tags.filter(e => e != tag)}
            let files = {...this.state.files}
            files[file.id] = file
            this.setState({
                files: files
            })
            window.socket.emit('removeTag', fileId, tag, (ack) => {
                console.log(ack)
                if (ack.payload) {
                    files = {...this.state.files}
                    files[fileId] = ack.payload
                    this.setState({
                        files: files
                    })
                }
            })
        }
    }

    closeModal = () => {
        this.setState({
            modal: {
                ...this.state.modal,
                active: false,
                textField: '',
                fileId: -1
            }
        })
    }

    // updateFile = (file) => {

    // }

    render() {
        let sortedKeys = []
        for (let key in this.state.files) {
            sortedKeys.push(key)
        }
        sortedKeys.sort()
        sortedKeys.reverse()

        let files = []
        for (let key in sortedKeys) {
            let value = this.state.files[key]
            files.push(value)
        }
        return (
            <>
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
                            {files.map((file) => {
                                return (
                                    <tr key={file.id}>
                                        <td onClick={() => {this.openFile(file.path)}}><a>{file.name}</a></td>
                                        <td onClick={() => {this.openFile(file.path)}}><a>{file.path}</a></td>
                                        <td>
                                            <div className='field is-grouped is-grouped-multiline'>
                                                {file.tags.map((tag) => {
                                                    return (
                                                        <div key={tag} className='control'>
                                                            <div className='tags are-small has-addons'>
                                                                <span className='tag is-info'>{tag}</span>
                                                                <a onClick={() => { this.removeTag(file.id, tag) }} className='tag is-delete'></a>
                                                            </div>
                                                        </div>
                                                    )
                                                })}
                                                <div className='control'>
                                                    <div className="tags are-small">
                                                        <a className='tag is-small' onClick={() => {this.activateModal(file.id)}}>
                                                            <span className="icon is-small">
                                                                <i className="fas fa-plus"></i>
                                                            </span>
                                                        </a>
                                                        {/* <span>GitHub</span> */}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        {/* <td>{file.suggested_tags}</td> */}
                                    </tr>
                                )
                            })}
                        </tfoot>
                    </table>
                </div>
                <Modal active={this.state.modal.active} close={this.closeModal}>
                    <div className='container is-fluid has-text-centered'>
                        <div className="field has-addons">
                            <div className="control is-expanded">
                                <input onKeyPress={(evt) => {evt.key === 'Enter' && this.addTag(this.state.modal.fileId, this.state.modal.textField)}} ref={input => input && input.focus()} className="input is-focused" type="text" placeholder="New Tag" value={this.state.modal.textField} onChange={evt => this.updateModalInputValue(evt)} />
                            </div>
                            <div className="control">
                                <a className="button is-info" onClick={() => {this.addTag(this.state.modal.fileId, this.state.modal.textField)}}>
                                    Add
                                </a>
                            </div>
                        </div>
                    </div>
                </Modal>
            </>
        )
    }

    updateModalInputValue = (evt) => {
        this.setState({
            modal: {...this.state.modal, textField: evt.target.value}
        })
    }
}

export default App;