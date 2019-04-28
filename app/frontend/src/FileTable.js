import React from 'react';
import moment from 'moment'

import 'bulma/css/bulma.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

import './table.css'

class FileTable extends React.Component {
    render() {
        return (
            <table className="table is-fullwidth tableFixedHead is-hoverable">
                <tfoot>
                    {this.props.files.map((file) => {
                        return (
                            <tr key={file.id}>
                                <td width='30%' onClick={() => {this.props.openFile(file.path)}}><a>{file.name}</a></td>
                                {/* <td onClick={() => {this.openFile(file.path)}}><a>{file.path}</a></td> */}
                                <td width='25%'>{moment(file.timestamp, 'YYYY-MM-DD HH:mm:ss.SSSSSS').format('MM/DD/YYYY HH:mm a')}</td>
                                <td width='45%'>
                                    {file.tags !== 'loading' && <div className='field is-grouped is-grouped-multiline'>
                                        {Object.keys(file.tags).map((tag) => {
                                            return (
                                                <div key={tag} className='control'>
                                                    <div className='tags are-small has-addons'>
                                                        <span className='tag is-info'>{tag}</span>
                                                        <a onClick={() => { this.props.removeTag(file.id, tag) }} className='tag is-delete'></a>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                        <div className='control'>
                                            <div className="tags are-small">
                                                <a className='tag is-small' onClick={() => {this.props.activateModal(file.id)}}>
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

                {/* moved to end because tags were showing on top of header */}
                <thead>
                    <tr>
                        <th width='30%'>File Name</th>
                        <th width='25%'>Date Added</th>
                        <th width='45%'>Fabels</th>
                    </tr>
                </thead>

            </table>
        )
    }
}
export default FileTable