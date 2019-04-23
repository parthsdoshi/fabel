import React from 'react';

class Modal extends React.Component {
    render() {
        let modalClass = 'modal'
        if (this.props.active) {
            modalClass = 'modal is-active'
        }
        return (
            <div className={modalClass}>
                <div className='modal-background' onClick={this.props.close}></div>
                <div className='modal-content'>
                    {this.props.children}
                </div>
                <button onClick={this.props.close} className="modal-close is-large" aria-label="close"></button>
            </div>
        )
    }
}

export default Modal