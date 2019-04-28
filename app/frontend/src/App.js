import React from 'react';
import io from 'socket.io-client'

import Modal from './Modal'
import FileTable from './FileTable'

import 'bulma/css/bulma.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

class App extends React.Component {
    constructor(props) {
        super(props)
        let test_files = {
            0: { 'id': 0, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            1: { 'id': 1, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            2: { 'id': 2, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            3: { 'id': 3, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            4: { 'id': 4, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            5: { 'id': 5, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            6: { 'id': 6, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            7: { 'id': 7, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            8: { 'id': 8, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            9: { 'id': 9, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            10: { 'id': 10, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            11: { 'id': 11, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            12: { 'id': 12, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            13: { 'id': 13, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            14: { 'id': 14, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            15: { 'id': 15, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            16: { 'id': 16, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            17: { 'id': 17, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            18: { 'id': 18, 'tags': 'loading', 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            19: { 'id': 19, 'tags': {'idk': 'idk', 'not lol': 'not lol'}, 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
            20: { 'id': 20, 'tags': {'idk': 'idk', 'lol': 'lol'}, 'timestamp': Date.now(), 'path': 'test/test/test', 'name': 'test' },
        }
        this.state = {
            files: {},
            modal: {
                active: false,
                fileId: -1,
                textField: ''
            },
            fileModal: {
                active: false
            },
            clickedTags: new Set()
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

    toggleTag = (tag) => {
        let newClickedTags = new Set(this.state.clickedTags)
        if (newClickedTags.has(tag)) {
            newClickedTags.delete(tag)
        } else {
            newClickedTags.add(tag)
        }

        this.setState({
            clickedTags: newClickedTags
        })
    }

    onDragOver = (evt) => {
        evt.preventDefault()
        this.setState({
            fileModal: {...this.state.fileModal, active: true}
        })
        // console.log(evt)
    }

    onDropped = (evt) => {
        evt.preventDefault()
        this.setState({
            fileModal: {...this.state.fileModal, active: false}
        })
        // console.log(evt.dataTransfer.files)
        // console.log(evt.dataTransfer.items[0].webkitGetAsEntry())
        if (window.socket) {
            window.socket.emit('openFileDialog', (ack) => {
                console.log(ack)
            })
        }
    }

    createFileDialog = () => {
        if (window.socket) {
            window.socket.emit('openFileDialog', (ack) => {
                console.log(ack)
            })
        }
    }

    // updateFile = (file) => {

    // }

    render() {
        let allTagsSet = new Set()

        let sortedKeys = []
        for (let key in this.state.files) {
            sortedKeys.push(parseInt(key))

            let tags = this.state.files[key].tags
            if (tags !== 'loading') {
                for (let tag of Object.keys(tags)) {
                    allTagsSet.add(tag)
                }
            }
        }
        sortedKeys.sort(function(a, b){return a-b})
        sortedKeys = sortedKeys.reverse()

        let allTags = []
        allTagsSet.forEach((v, v2, set) => {
            let c = 'is-white'
            if (this.state.clickedTags.has(v)) {
                c = 'is-dark'
            }
            allTags.push({
                tag: v,
                class: c
            })
        })

        let files = []
        for (let i = 0; i < sortedKeys.length; i++) {
            let key = sortedKeys[i]
            key = key.toString()

            let file = this.state.files[key]
            let fileTags = file['tags']
            let remove = false
            if (fileTags !== 'loading') {
                for (let tag of this.state.clickedTags) {
                    // not all clicked tags in this file
                    if (!(tag in fileTags)) {
                        remove = true
                        break
                    }
                }
            } else if (this.state.clickedTags.size !== 0) {
                continue
            }

            if (remove) {
                continue
            }
            files.push(file)
        }

        return (
            <>
                <div className='container is-fluid' onDrop={this.onDropped} onDragOver={this.onDragOver}>
                    {/* <table className="table is-fullwidth" style={tableFixedHeadStyle}> */}
                    <section className='hero is-primary is-bold'>
                        <div className='hero-body'>
                            <div className='container'>
                                <nav className='level'>
                                    <div className='level-left'>
                                        {allTags.length > 0 && <h1 className='title'>Filter by Fabels:</h1>}
                                        {allTags.length === 0 && <h1 className='title'>Fabel</h1>}
                                    </div>
                                    <div className='level-right'>
                                        <div className='level-item'>
                                            <a class="button is-rounded" onClick={this.createFileDialog}>
                                                <span className='icon'>
                                                    <i class="fas fa-plus"></i>
                                                </span>
                                                <span>Add Files</span>
                                            </a>
                                        </div>
                                    </div>
                                </nav>
                                <div className='control'>
                                    <div className='tags are-small'>
                                        {allTags.map(tagDict => {
                                            return (
                                                <a key={tagDict.tag} onClick={() => { this.toggleTag(tagDict.tag) }} className={tagDict.class + ' tag'}>{tagDict.tag}</a>
                                            )
                                        })}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>
                    <div className='box'>
                        {files.length > 0 && 
                            <FileTable files={files} activateModal={this.activateModal} removeTag={this.removeTag} openFile={this.openFile} />
                        }
                        {files.length === 0 &&
                            <article class="message">
                                <div class="message-header">
                                    Looks like there aren't any files here.
                                </div>
                                {this.state.clickedTags.size === 0 && <div class="message-body">
                                    You can add some by clicking Add Files on the top right or just download something from Chrome!
                                </div>}
                                {this.state.clickedTags.size > 0 && <div class="message-body">
                                    No files match your selected fabels :(
                                </div>}
                            </article>
                        }
                    </div>
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
                <div onDragOver={this.onDragOver} onDrop={this.onDropped}>
                <Modal active={this.state.fileModal.active} close={this.closeFileModal}>
                    <div className='container is-fluid has-text-centered'>
                        <p>Drop files here.</p>
                    </div>
                </Modal>
                </div>
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