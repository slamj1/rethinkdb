#!/usr/bin/env python
import sys

"""This script is used to generate the mailbox templates in
`rethinkdb/src/rpc/mailbox/typed.hpp`. It is meant to be run as follows
(assuming that the current directory is `rethinkdb/src/`):

$ ../scripts/generate_rpc_templates.py > rpc/mailbox/typed.hpp

"""

def generate_async_message_template(nargs):

    def csep(template):
        return ", ".join(template.replace("#", str(i)) for i in xrange(nargs))

    def cpre(template):
        return "".join(", " + template.replace("#", str(i)) for i in xrange(nargs))

    print
    print "template<" + csep("class arg#_t") + ">"
    print "class mailbox_addr_t< void(" + csep("arg#_t") + ") > {"
    print "public:"
    print "    bool is_nil() const { return addr.is_nil(); }"
    print "    peer_id_t get_peer() const { return addr.get_peer(); }"
    print
    print "    friend class mailbox_t< void(" + csep("arg#_t") + ") >;"
    print
    print "    RDB_MAKE_ME_SERIALIZABLE_1(addr)"
    print "private:"
    if nargs == 0:
        print "    friend void send(mailbox_manager_t*, mailbox_addr_t);"
    else:
        print "    template<" + csep("class a#_t") + ">"
        print "    friend void send(mailbox_manager_t*, typename mailbox_t< void(" + csep("a#_t") + ") >::address_t" + cpre("const a#_t&") + ");"
    print "    raw_mailbox_t::address_t addr;"
    print "};"
    print
    print "template<" + csep("class arg#_t") + ">"
    print "class mailbox_t< void(" + csep("arg#_t") + ") > {"
    print "public:"
    print "    typedef mailbox_addr_t< void(" + csep("arg#_t") + ") > address_t;"
    print
    print "    mailbox_t(mailbox_manager_t *manager, const boost::function< void(" + csep("arg#_t") + ") > &f, mailbox_callback_mode_t cbm = mailbox_callback_mode_coroutine) :"
    print "        fun(f), callback_mode(cbm), mailbox(manager, boost::bind(&mailbox_t::on_message, this, _1))"
    print "        { }"
    print
    print "    address_t get_address() {"
    print "        address_t a;"
    print "        a.addr = mailbox.get_address();"
    print "        return a;"
    print "    }"
    print
    print "private:"
    if nargs == 0:
        print "    friend void send(mailbox_manager_t*, address_t);"
    else:
        print "    template<" + csep("class a#_t") + ">"
        print "    friend void send(mailbox_manager_t*, typename mailbox_t< void(" + csep("a#_t") + ") >::address_t" + cpre("const a#_t&") + ");"
    print "    static void write(write_stream_t *stream" + cpre("const arg#_t &arg#") + ") {"
    print "        write_message_t msg;"
    for i in xrange(nargs):
        print "        msg << arg%d;" % i
    print "        int res = send_write_message(stream, &msg);"
    print "        if (res) { throw fake_archive_exc_t(); }"
    print "    }"
    print "    void on_message(%sread_stream_t *stream) {" % ("" if nargs > 0 else "UNUSED ")
    for i in xrange(nargs):
        print "        arg%d_t arg%d;" % (i, i)

    for i in xrange(nargs):
        print "        %sres = deserialize(stream, &arg%d);" % ("int " if i == 0 else "", i)
        print "        if (res) { throw fake_archive_exc_t(); }"
    print "        if (callback_mode == mailbox_callback_mode_coroutine) {"
    print "            coro_t::spawn_sometime(boost::bind(fun" + cpre("arg#") + "));"
    print "        } else {"
    print "            fun(" + csep("arg#") + ");"
    print "        }"
    print "    }"
    print
    print "    boost::function< void(" + csep("arg#_t") + ") > fun;"
    print "    mailbox_callback_mode_t callback_mode;"
    print "    raw_mailbox_t mailbox;"
    print "};"
    print
    if nargs == 0:
        print "inline"
    else:
        print "template<" + csep("class arg#_t") + ">"
    print "void send(mailbox_manager_t *src, " + ("typename " if nargs > 0 else "") + "mailbox_t< void(" + csep("arg#_t") + ") >::address_t dest" + cpre("const arg#_t &arg#") + ") {"
    print "    send(src, dest.addr,"
    print "        boost::bind(&mailbox_t< void(" + csep("arg#_t") + ") >::write, _1" + cpre("boost::ref(arg#)") + "));"
    print "}"
    print

if __name__ == "__main__":

    print "#ifndef RPC_MAILBOX_TYPED_HPP_"
    print "#define RPC_MAILBOX_TYPED_HPP_"
    print

    print "/* This file is automatically generated by '%s'." % " ".join(sys.argv)
    print "Please modify '%s' instead of modifying this file.*/" % sys.argv[0]
    print

    print "#include \"containers/archive/archive.hpp\""
    print "#include \"rpc/serialize_macros.hpp\""
    print "#include \"rpc/mailbox/mailbox.hpp\""
    print

    print "/* If you pass `mailbox_callback_mode_coroutine` to the `mailbox_t` "
    print "constructor, it will spawn the callback in a new coroutine. If you "
    print "`mailbox_callback_mode_inline`, it will call the callback inline "
    print "and the callback must not block. The former is the default for "
    print "historical reasons, but the latter is better. Eventually the former "
    print "will go away. */"
    print "enum mailbox_callback_mode_t {"
    print "    mailbox_callback_mode_coroutine,"
    print "    mailbox_callback_mode_inline"
    print "};"
    print

    print "template<class invalid_proto_t> class mailbox_t {"
    print "    /* If someone tries to instantiate `mailbox_t` "
    print "    incorrectly, this should cause an error. */"
    print "    typename invalid_proto_t::you_are_using_mailbox_t_incorrectly foo;"
    print "};"
    print
    print "template<class invalid_proto_t> class mailbox_addr_t {"
    print "    // If someone tries to instantiate mailbox_addr_t incorrectly,"
    print "    // this should cause an error."
    print "    typename invalid_proto_t::you_are_using_mailbox_addr_t_incorrectly foo;"
    print "};"

    for nargs in xrange(15):
        generate_async_message_template(nargs)

    print "#endif // RPC_MAILBOX_TYPED_HPP_"
