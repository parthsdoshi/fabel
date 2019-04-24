import React from 'react';
import io from 'socket.io-client'
import Modal from './Modal'

import 'bulma/css/bulma.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

import './table.css'

class App extends React.Component {
    constructor(props) {
        super(props)
        let test_files = {
            0: { 'id': 0, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            1: { 'id': 1, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            2: { 'id': 2, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            3: { 'id': 3, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            4: { 'id': 4, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            5: { 'id': 5, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            6: { 'id': 6, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            7: { 'id': 7, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            8: { 'id': 8, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            9: { 'id': 9, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            10: { 'id': 10, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            11: { 'id': 11, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            12: { 'id': 12, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            13: { 'id': 13, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            14: { 'id': 14, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            15: { 'id': 15, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            16: { 'id': 16, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            17: { 'id': 17, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            18: { 'id': 18, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            19: { 'id': 19, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            20: { 'id': 20, 'tags': 'loading', 'date': Date.now(), 'path': 'test/test/test', 'name': 'test' },
        }
        this.state = {
            files: {},
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

            return
            socket.emit('getAllFiles', (files) => {
                console.log(files)
                if (files['error'] === 0) {
                    this.setState({
                        files: files['payload']
                    })
                }
                socket.on('newFile', (file) => {
                    let files = {...this.state.files}
                    file['tags'] = 'loading'
                    files[file.id] = file
                    this.setState({
                        files: files
                    })
                })

                socket.on('updateFile', (file) => {
                    let files = {...this.state.files}
                    files[file.id] = file
                    this.setState({
                        files: files
                    })
                })

                socket.on('removeFile', (uniqueId) => {
                    // should probably notify user in a modal or smthg
                    if (uniqueId in this.state.files) {
                        let files = {...this.state.files}
                        delete files[uniqueId]
                        this.setState({
                            files: files
                        })
                    } else {
                        // handle error
                    }
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
            // let file = {...this.state.files[fileId], tags: [...this.state.files[fileId].tags, tag]}
            // let files = {...this.state.files}
            // files[file.id] = file
            // this.setState({
            //     files: files
            // })
            let file = {...this.state.files[fileId], tags: 'loading'}
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
            // let file = {...this.state.files[fileId], tags: this.state.files[fileId].tags.filter(e => e !== tag)}
            // let files = {...this.state.files}
            // files[file.id] = file
            // this.setState({
            //     files: files
            // })
            let file = {...this.state.files[fileId], tags: 'loading'}
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
        // .tableFixHead    { overflow-y: auto; height: 100px}
        // .tableFixHead th { position: sticky; top: 0; }
        let tableFixedHeadStyle = {
            overflowY: 'auto',
            height: '100px'
        }
        let tableFixedHeadThStyle = {
            position: 'sticky',
            top: 0,
            background: 'white',
            backgroundColor: 'white'
        }

        let sortedKeys = []
        for (let key in this.state.files) {
            sortedKeys.push(parseInt(key))
        }
        sortedKeys.sort(function(a, b){return a-b})
        sortedKeys = sortedKeys.reverse()

        let files = []
        for (let i = 0; i < sortedKeys.length; i++) {
            let key = sortedKeys[i]
            key = key.toString()
            let value = this.state.files[key]
            files.push(value)
        }
        return (
            <>
                <div className='container is-fluid'>
                    {/* <table className="table is-fullwidth" style={tableFixedHeadStyle}> */}
                    <table className="table is-fullwidth tableFixedHead">
                        <thead>
                            <tr>
                                <th>File Name</th>
                                <th>File Path</th>
                                <th>Tags</th>
                                {/* <th style={tableFixedHeadThStyle}>File Name</th> */}
                                {/* <th style={tableFixedHeadThStyle}>File Path</th> */}
                                {/* <th style={tableFixedHeadThStyle}>Tags</th> */}
                            </tr>
                        </thead>
                        <tfoot>
                            {files.map((file) => {
                                return (
                                    <tr key={file.id}>
                                        <td onClick={() => {this.openFile(file.path)}}><a>{file.name}</a></td>
                                        <td onClick={() => {this.openFile(file.path)}}><a>{file.path}</a></td>
                                        <td>
                                            {file.tags !== 'loading' && <div className='field is-grouped is-grouped-multiline'>
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
                                                    </div>
                                                </div>
                                            </div>}
                                            {file.tags === 'loading' && <div className='level'><div className='level-item'>
                                                <progress className="progress is-small is-info"/>
                                            </div></div>}
                                        </td>
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